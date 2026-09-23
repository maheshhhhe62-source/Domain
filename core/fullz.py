"""
Spidey Core — Fullz Extractor
100% same as Telegram bot
CC + Cardholder data from SQLMap CSV dumps
"""
import os
import re
import csv
import json
import logging

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
#  REGEX PATTERNS — 100% same as bot
# ═══════════════════════════════════════════════════════════════════════════

_CARD_RE = re.compile(
    r"\b(4[0-9]{12}(?:[0-9]{3,6})?|5[1-5][0-9]{14}"
    r"|2(?:2[2-9][1-9]|[3-6]\d{2}|7(?:[01]\d|20))\d{12}"
    r"|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12}"
    r"|(?:2131|1800|35\d{3})\d{11})\b"
)

_EXP_RE = re.compile(r"\b(0?[1-9]|1[0-2])[/\-|,](2[0-9]|20[0-9]{2})\b")

_CVV_RE = re.compile(r"\b([0-9]{3,4})\b")


# ═══════════════════════════════════════════════════════════════════════════
#  FULLZ FIELD ALIASES — 100% same
# ═══════════════════════════════════════════════════════════════════════════
FULLZ_FIELD_ALIASES = {
    "cc_number":  ["card_number","cardnumber","card_num","cc_number","ccnumber",
                   "credit_card","creditcard","card_no","card","cc","pan"],
    "cvv":        ["cvv","cvc","cvv2","cvc2","security_code","card_code","verification_code","cvn"],
    "exp_month":  ["exp_month","expiry_month","expm","card_exp_month","expiration_month","month"],
    "exp_year":   ["exp_year","expiry_year","expy","card_exp_year","expiration_year","year"],
    "exp_full":   ["expiry","expiry_date","exp_date","expiration","card_expiry","card_exp"],
    "holder_name":["cardholder","card_holder","name_on_card","holder_name","full_name",
                   "first_name","fname","customer_name","account_holder","card_name"],
    "last_name":  ["last_name","lname","surname","family_name","lastname"],
    "address":    ["billing_address","address","address1","address_1","street","street_address",
                   "home_address","addr","addr1","addressline","address_line_1"],
    "address2":   ["address2","address_2","addr2","addressline2","address_line_2"],
    "city":       ["city","town","billing_city","city_name","locality"],
    "state":      ["state","province","region","billing_state","state_name"],
    "zip":        ["zip","zip_code","zipcode","postal","postal_code","postcode","billing_zip",
                   "billing_postal_code"],
    "country":    ["country","country_code","billing_country","nation","iso_country"],
    "phone":      ["phone","phone_number","mobile","mobile_number","cell","telephone",
                   "tel","contact_number","phone_no","billing_phone","cellphone"],
    "email":      ["email","email_address","mail","user_email","member_email","account_email",
                   "contact_email","primary_email","billing_email"],
    "dob":        ["dob","birthdate","birth_date","date_of_birth","birthday"],
    "ssn":        ["ssn","social_security","social_security_number","sin","national_id","tax_id"],
    "user_id":    ["user_id","userid","customer_id","customerid","member_id","account_id",
                   "client_id","uid","profile_id","account_number"],
}


# ═══════════════════════════════════════════════════════════════════════════
#  AUTO DUMP PAIRS — 100% same (bot mein bhi ye hi tha)
# ═══════════════════════════════════════════════════════════════════════════
AUTO_DUMP_PAIRS = [
    ("email","password","email:pass"), ("email","passwd","email:pass"),
    ("username","password","user:pass"), ("user","password","user:pass"),
    ("login","password","login:pass"), ("login","passwd","login:pass"),
    ("username","passwd","user:pass"), ("user","pass","user:pass"),
    ("email","pwd","email:pwd"), ("username","pwd","user:pwd"),
    ("card_number","cvv","card:cvv"), ("cc","cvv","cc:cvv"),
    ("username","token","user:token"), ("email","token","email:token"),
]


# ═══════════════════════════════════════════════════════════════════════════
#  HELPERS — 100% same
# ═══════════════════════════════════════════════════════════════════════════
def _normalize_col(col: str) -> str:
    """Normalize column name"""
    return re.sub(r"[^a-z0-9_]", "", str(col).lower())


def _match_field(column_name: str) -> str:
    """Match DB column to fullz field"""
    cn = _normalize_col(column_name)
    for field, aliases in FULLZ_FIELD_ALIASES.items():
        if cn in aliases:
            return field
    for field, aliases in FULLZ_FIELD_ALIASES.items():
        for alias in aliases:
            if alias in cn or cn in alias:
                return field
    return ""


def _row_to_dict(header_row, data_row) -> dict:
    """Convert CSV header + row → dict"""
    out = {}
    for i, col in enumerate(header_row):
        if i < len(data_row):
            out[col] = str(data_row[i]).strip()
    return out


def _detect_header(row) -> bool:
    """Detect if row is a header row"""
    if not row:
        return False
    text = " ".join(str(c).lower() for c in row)
    header_hints = ["id","name","email","card","address","phone","password","user",
                    "date","zip","city","amount","order","product","price","status"]
    hits = sum(1 for h in header_hints if h in text)
    return hits >= 3 and not _CARD_RE.search(text)


def _find_header_row(rows: list) -> int:
    """Find header row index in CSV rows"""
    for i in range(min(3, len(rows))):
        if _detect_header(rows[i]):
            return i
    return -1


# ═══════════════════════════════════════════════════════════════════════════
#  CARD EXTRACTION — 100% same as bot
# ═══════════════════════════════════════════════════════════════════════════
def _extract_cards_from_text(text: str) -> list:
    """Extract CC numbers from any text. Returns list of 'cc|mm|yy|cvv'"""
    cards, seen = [], set()
    for m in _CARD_RE.finditer(text):
        cn = m.group(1)
        ctx = text[max(0, m.start()-60):m.start()+120]
        em = _EXP_RE.search(ctx)
        if em:
            month = em.group(1).zfill(2)
            year = em.group(2)
            if len(year) == 4:
                year = year[2:]
        else:
            month, year = "??", "??"
        cvv = "???"
        t3, t4 = cn[-3:], cn[-4:]
        for c in _CVV_RE.findall(text[m.end():m.end()+80]):
            if c == year or c == ("20" + year):
                continue
            if c == t3 or c == t4:
                continue
            if len(c) in (3, 4):
                cvv = c
                break
        entry = f"{cn}|{month}|{year}|{cvv}"
        if entry not in seen:
            seen.add(entry)
            cards.append(entry)
    return cards


def _extract_cards_from_api_data(data_list: list) -> list:
    """Extract cards from SQLMap API data (list of dicts). Same as bot."""
    cards, seen = [], set()
    for item in data_list:
        val = item.get("value", "")
        text = json.dumps(val) if not isinstance(val, str) else val
        for c in _extract_cards_from_text(text):
            if c not in seen:
                seen.add(c)
                cards.append(c)
    return cards


def _extract_cards_from_csv_dir(output_dir: str) -> list:
    """Extract all CC numbers from all CSVs in directory. Same as bot."""
    cards, seen = [], set()
    for root, _, files in os.walk(output_dir):
        for fn in files:
            if not fn.lower().endswith(".csv"):
                continue
            try:
                with open(os.path.join(root, fn), encoding="utf-8", errors="ignore") as f:
                    for row in csv.reader(f):
                        for c in _extract_cards_from_text(" ".join(str(x) for x in row)):
                            if c not in seen:
                                seen.add(c)
                                cards.append(c)
            except Exception:
                pass
    return cards


# ═══════════════════════════════════════════════════════════════════════════
#  FULLZ RECORD CLASS — 100% same
# ═══════════════════════════════════════════════════════════════════════════
class FullzRecord:
    __slots__ = ("cc_number","cvv","exp_month","exp_year","holder_name",
                 "address","address2","city","state","zip","country",
                 "phone","email","dob","ssn","user_id","source_table","raw_row")

    def __init__(self):
        for s in self.__slots__:
            setattr(self, s, "")

    def to_cc_format(self) -> str:
        """cc|mm|yy|cvv"""
        if not self.cc_number:
            return ""
        return f"{self.cc_number}|{self.exp_month or '??'}|{self.exp_year or '??'}|{self.cvv or '???'}"

    def to_fullz_format(self) -> str:
        """Full fullz format (15 fields)"""
        return "|".join([
            self.cc_number or "?",
            self.exp_month or "??",
            self.exp_year or "??",
            self.cvv or "???",
            self.holder_name or "?",
            self.address or "?",
            self.address2 or "-",
            self.city or "?",
            self.state or "?",
            self.zip or "?",
            self.country or "?",
            self.phone or "?",
            self.email or "?",
            self.dob or "-",
            self.ssn or "-",
        ])

    def is_complete(self) -> bool:
        return bool(self.cc_number and (self.holder_name or self.address) and self.zip)

    def has_card(self) -> bool:
        return bool(self.cc_number)


# ═══════════════════════════════════════════════════════════════════════════
#  FULLZ ROW PARSER — 100% same
# ═══════════════════════════════════════════════════════════════════════════
def _parse_fullz_row(row_dict: dict, source_table: str = "") -> FullzRecord:
    """Parse a CSV row dict → FullzRecord"""
    rec = FullzRecord()
    rec.source_table = source_table
    rec.raw_row = "|".join(f"{k}={v}" for k, v in row_dict.items())

    # Match known columns
    for col, val in row_dict.items():
        field = _match_field(col)
        if not field or not val or val.lower() in ("null","none","","n/a","na"):
            continue
        if not getattr(rec, field):
            setattr(rec, field, val)

    # Parse expiry from single field
    expf = (row_dict.get("expiry") or row_dict.get("expiry_date")
            or row_dict.get("exp_date") or row_dict.get("card_expiry"))
    if expf and (not rec.exp_month or not rec.exp_year):
        m = re.match(r"(\d{1,2})\s*[/\-]\s*(\d{2,4})", str(expf))
        if m:
            rec.exp_month = m.group(1).zfill(2)
            y = m.group(2)
            rec.exp_year = y[-2:] if len(y) == 4 else y

    # Fallback: find CC in any cell
    if not rec.cc_number:
        for col, val in row_dict.items():
            cm = _CARD_RE.search(str(val))
            if cm:
                rec.cc_number = cm.group(1)
                break

    # Fallback: find CVV in any cell
    if not rec.cvv:
        for col, val in row_dict.items():
            cl = _normalize_col(col)
            if "cvv" in cl or "cvc" in cl or "security" in cl or "verif" in cl:
                cm = re.search(r"\b(\d{3,4})\b", str(val))
                if cm:
                    rec.cvv = cm.group(1)
                    break

    # Clean phone + zip
    if rec.phone:
        rec.phone = re.sub(r"[^\d+\-() ]", "", rec.phone).strip()
    if rec.zip:
        rec.zip = re.sub(r"[^\d\-]", "", rec.zip)

    return rec


# ═══════════════════════════════════════════════════════════════════════════
#  CSV EXTRACTION — 100% same
# ═══════════════════════════════════════════════════════════════════════════
def extract_fullz_from_csv(csv_path: str, source_table: str = "") -> list:
    """Extract fullz records from a single CSV file"""
    out = []
    try:
        with open(csv_path, encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            rows = [r for r in reader if r]
            if not rows:
                return []

            hdr_idx = _find_header_row(rows)

            # No header detected → parse each row as freeform
            if hdr_idx < 0:
                for row in rows:
                    text = " ".join(str(c) for c in row)
                    for cc in _extract_cards_from_text(text):
                        r = FullzRecord()
                        parts = cc.split("|")
                        r.cc_number, r.exp_month, r.exp_year, r.cvv = parts
                        for cell in row:
                            s = str(cell).strip()
                            if re.match(r"^\d{5}(-\d{4})?$", s) and not r.zip:
                                r.zip = s
                            elif re.match(r"^\+?\d{10,15}$", s) and not r.phone:
                                r.phone = s
                        out.append(r)
                return out

            # Header detected → parse rows normally
            header = rows[hdr_idx]
            for data_row in rows[hdr_idx + 1:]:
                if not data_row or all(not str(c).strip() for c in data_row):
                    continue
                row_dict = _row_to_dict(header, data_row)
                rec = _parse_fullz_row(row_dict, source_table=source_table)
                if rec.has_card() or (rec.holder_name and rec.zip):
                    out.append(rec)
    except Exception as e:
        logger.debug(f"fullz parse error {csv_path}: {e}")
    return out


def extract_fullz_from_dir(output_dir: str) -> list:
    """Extract all fullz from directory (recursive CSV scan). Same as bot."""
    all_recs = []
    for root, _, files in os.walk(output_dir):
        for fn in files:
            if fn.lower().endswith(".csv"):
                table_name = os.path.splitext(fn)[0]
                recs = extract_fullz_from_csv(os.path.join(root, fn), source_table=table_name)
                all_recs.extend(recs)

    # Dedup
    seen = set()
    deduped = []
    for r in all_recs:
        key = (r.cc_number, r.holder_name, r.zip, r.email)
        if r.cc_number and key not in seen:
            seen.add(key)
            deduped.append(r)
        elif not r.cc_number and (r.holder_name or r.email):
            k2 = (r.holder_name, r.email, r.zip)
            if k2 not in seen:
                seen.add(k2)
                deduped.append(r)
    return deduped


# ═══════════════════════════════════════════════════════════════════════════
#  OUTPUT FORMATTING — 100% same
# ═══════════════════════════════════════════════════════════════════════════
def fullz_records_to_lines(records: list, format: str = "full") -> list:
    """Convert list of records → list of formatted lines (deduped)"""
    lines = []
    seen = set()
    for r in records:
        line = r.to_cc_format() if format == "cc" else r.to_fullz_format()
        if line and line not in seen:
            seen.add(line)
            lines.append(line)
    return lines


def fullz_summary(records: list) -> str:
    """Human-readable summary. Same as bot."""
    total = len(records)
    with_cc = sum(1 for r in records if r.has_card())
    complete = sum(1 for r in records if r.is_complete())
    with_phone = sum(1 for r in records if r.phone)
    with_email = sum(1 for r in records if r.email)
    with_addr = sum(1 for r in records if r.address)
    with_name = sum(1 for r in records if r.holder_name)
    with_zip = sum(1 for r in records if r.zip)
    with_cvv = sum(1 for r in records if r.cvv and r.cvv != "???")
    return (
        f"💳 Total records: `{total}`\n"
        f"🔢 With CC number: `{with_cc}`\n"
        f"✅ Complete (CC+name+addr+zip): `{complete}`\n"
        f"🔐 With CVV: `{with_cvv}`\n"
        f"👤 With name: `{with_name}`\n"
        f"🏠 With address: `{with_addr}`\n"
        f"📮 With ZIP: `{with_zip}`\n"
        f"📞 With phone: `{with_phone}`\n"
        f"📧 With email: `{with_email}`"
    )


# ═══════════════════════════════════════════════════════════════════════════
#  UTILITY FUNCTIONS — 100% same
# ═══════════════════════════════════════════════════════════════════════════
def detect_auto_pairs(tables: list) -> list:
    """Detect auto-dumpable column pairs (email:pass, user:pass, etc.)"""
    out = []
    for tbl in tables:
        tname = tbl.get("table", "") if isinstance(tbl, dict) else str(tbl)
        cols = [str(c).lower() for c in (
            tbl.get("columns", []) if isinstance(tbl, dict) else []
        )]
        for kw1, kw2, pname in AUTO_DUMP_PAIRS:
            if any(kw1 in c for c in cols) and any(kw2 in c for c in cols):
                c1 = next((c for c in cols if kw1 in c), kw1)
                c2 = next((c for c in cols if kw2 in c), kw2)
                out.append((tname, c1, c2, pname))
    return out