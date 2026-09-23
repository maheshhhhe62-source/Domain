"""
Spidey Core — URL Finder
100% same as Telegram bot
Dorks → URLs (via 8 engines + DDGS)
"""
import asyncio
import aiohttp
import random
import re
import base64
import time
import threading as _threading
import concurrent.futures
from urllib.parse import urlparse, parse_qs, parse_qsl, urlencode, urlunparse, quote_plus, unquote

from bs4 import BeautifulSoup


# ═══════════════════════════════════════════════════════════════════════════
#  THREAD POOL — 100% same
# ═══════════════════════════════════════════════════════════════════════════
_THREAD_POOL = concurrent.futures.ThreadPoolExecutor(max_workers=32)


# ═══════════════════════════════════════════════════════════════════════════
#  GLOBAL CONNECTOR — 100% same
# ═══════════════════════════════════════════════════════════════════════════
_GLOBAL_CONNECTOR = None


def _get_connector():
    global _GLOBAL_CONNECTOR
    if _GLOBAL_CONNECTOR is None or _GLOBAL_CONNECTOR.closed:
        _GLOBAL_CONNECTOR = aiohttp.TCPConnector(
            limit=300, limit_per_host=15,
            ttl_dns_cache=300, force_close=False,
            enable_cleanup_closed=True
        )
    return _GLOBAL_CONNECTOR


# ═══════════════════════════════════════════════════════════════════════════
#  DDGS COOLDOWN — 100% same
# ═══════════════════════════════════════════════════════════════════════════
_ddgs_lock = _threading.Lock()
_ddgs_consecutive_empty = 0
_ddgs_cooldown_until = 0.0
_DDGS_EMPTY_THRESHOLD = 10
_DDGS_COOLDOWN_SECS = 45


def _ddgs_record_empty():
    global _ddgs_consecutive_empty, _ddgs_cooldown_until
    with _ddgs_lock:
        _ddgs_consecutive_empty += 1
        if _ddgs_consecutive_empty >= _DDGS_EMPTY_THRESHOLD:
            _ddgs_cooldown_until = time.time() + _DDGS_COOLDOWN_SECS
            _ddgs_consecutive_empty = 0


def _ddgs_record_success():
    global _ddgs_consecutive_empty
    with _ddgs_lock:
        _ddgs_consecutive_empty = 0


def _ddgs_wait_if_coolingdown():
    r = _ddgs_cooldown_until - time.time()
    if r > 0:
        time.sleep(r + 0.5)


# ═══════════════════════════════════════════════════════════════════════════
#  HEADERS — 100% same
# ═══════════════════════════════════════════════════════════════════════════
HEADERS_LIST = [
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
     "Accept-Language": "en-US,en;q=0.9", "Accept-Encoding": "gzip, deflate",
     "Connection": "keep-alive", "Cache-Control": "no-cache"},
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
     "Accept-Language": "en-GB,en;q=0.9", "Accept-Encoding": "gzip, deflate",
     "Connection": "keep-alive"},
    {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
     "Accept-Language": "en-US,en;q=0.5", "Accept-Encoding": "gzip, deflate",
     "Connection": "keep-alive"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
     "Accept-Language": "de-DE,de;q=0.9,en;q=0.5", "Accept-Encoding": "gzip, deflate",
     "Connection": "keep-alive"},
    {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
     "Accept-Language": "en-US,en;q=0.9", "Accept-Encoding": "gzip, deflate",
     "Connection": "keep-alive"},
]


# ═══════════════════════════════════════════════════════════════════════════
#  BLACKLIST — 100% same
# ═══════════════════════════════════════════════════════════════════════════
BLACKLIST_DOMAINS = {
    "google.com","google.co.uk","google.co.in","googleapis.com","googleusercontent.com",
    "gstatic.com","googlesyndication.com","bing.com","msn.com","yahoo.com","yimg.com",
    "duckduckgo.com","ddg.gg","ask.com","baidu.com","yandex.com","yandex.ru",
    "startpage.com","searxng.org","mojeek.com","facebook.com","fb.com","fbcdn.net",
    "instagram.com","twitter.com","x.com","t.co","tiktok.com","snapchat.com",
    "linkedin.com","pinterest.com","telegram.org","telegram.me","whatsapp.com",
    "discord.com","discord.gg","twitch.tv","reddit.com","redd.it","quora.com",
    "youtube.com","youtu.be","ytimg.com","vimeo.com","doubleclick.net","adnxs.com",
    "googletagmanager.com","scorecardresearch.com","quantserve.com","outbrain.com",
    "taboola.com","cloudflare.com","fastly.net","cdn.jsdelivr.net","cdnjs.cloudflare.com",
    "unpkg.com","jsdelivr.net","bit.ly","tinyurl.com","goo.gl","ow.ly","t.ly","rb.gy",
    "archive.org","web.archive.org","gravatar.com",
    "microsoft.com","office.com","office365.com","live.com","outlook.com","hotmail.com",
    "microsoftonline.com","azure.com","azurewebsites.net","windowsazure.com",
    "sharepoint.com","onedrive.com","skype.com","techcommunity.microsoft.com",
    "gmail.com","drive.google.com","docs.google.com","maps.google.com","play.google.com",
    "amazon.com","amazon.co.uk","amazon.in","amazon.de","amazonaws.com","aws.amazon.com",
    "awsstatic.com","apple.com","icloud.com","itunes.apple.com","apps.apple.com",
    "ebay.com","etsy.com","aliexpress.com","alibaba.com","walmart.com","target.com",
    "bestbuy.com","costco.com","shopify.com","bigcommerce.com","booking.com","expedia.com",
    "airbnb.com","tripadvisor.com","hotels.com","kayak.com","trivago.com","priceline.com",
    "agoda.com","vrbo.com","paypal.com","stripe.com","square.com","bankofamerica.com",
    "chase.com","wellsfargo.com","citibank.com","americanexpress.com","capitalone.com",
    "discover.com","usbank.com","tdbank.com","truist.com","creditkarma.com","nerdwallet.com",
    "mint.com","experian.com","equifax.com","transunion.com","intuit.com","turbotax.intuit.com",
    "irs.gov","usa.gov","gov.uk","data.gov","studentaid.gov","ed.gov","ohio.gov",
    "netflix.com","hulu.com","disneyplus.com","hbomax.com","spotify.com","soundcloud.com",
    "poki.com","roblox.com","steam.com","steampowered.com","epicgames.com","ea.com",
    "bbc.com","bbc.co.uk","cnn.com","nytimes.com","theguardian.com","reuters.com",
    "apnews.com","forbes.com","businessinsider.com","techcrunch.com","github.com",
    "gitlab.com","stackoverflow.com","stackexchange.com","medium.com","dev.to",
    "npm.js.org","pypi.org","docs.python.org","notion.so","airtable.com","slack.com",
    "zoom.us","grammarly.com","canva.com","figma.com","dropbox.com","box.com",
    "zillow.com","realtor.com","redfin.com","apartments.com","trulia.com","craigslist.org",
    "yelp.com","angi.com","homedepot.com","lowes.com","staples.com","officedepot.com",
    "adobe.com","salesforce.com","hubspot.com","zendesk.com","xe.com","transferwise.com",
    "wise.com","kiplinger.com","thecollegeinvestor.com","wallethub.com",
    "merriam-webster.com","dictionary.com","cambridge.org","scheels.com",
    "dickssportinggoods.com","rei.com",
}


JUNK_EXT = re.compile(
    r"\.(css|js|png|jpg|jpeg|gif|ico|svg|webp|woff|woff2|ttf|eot|xml|json|zip|exe|dmg|apk|pdf|doc|docx|xls|xlsx|csv|mp4|mp3|avi|mov|mkv|flv|swf|iso|tar|gz|rar|7z)(\?|$)",
    re.I
)
JUNK_URL_PATTERNS = re.compile(
    r"(doubleclick|adservice|pagead|adsense|googletagmanager|/redir\?|/redirect\?|/click\?|/trk\?|/track\?|/affiliate/|/aff/|/banner/|/pixel/|/beacon/|/ads/|ad\.php|/ad/\d)",
    re.I
)
HIGH_VALUE = re.compile(
    r"(payment|checkout|billing|invoice|transaction|receipt|order|cart|subscribe|subscription|membership|upgrade|refund|gateway|paypal|stripe|razorpay|authorize|braintree|login|signin|account|dashboard|profile|admin|member|creditcard|credit.card|debit|cardinfo|buy|purchase|shop|plan|register|signup)",
    re.I
)


# ═══════════════════════════════════════════════════════════════════════════
#  DORK CLEANER — 100% same
# ═══════════════════════════════════════════════════════════════════════════
def clean_dork_for_search(dork: str) -> str:
    d = dork.replace("\\", " ")
    d = re.sub(r'\bsite:\.?[a-zA-Z]{2}\b(?![\w.])', ' ', d)
    d = re.sub(r"\|\.\s*>", " ", d)
    d = re.sub(r"\d\s*\|\s*\d\s*\|\s*\d", " ", d)
    d = d.replace("|", " ").replace("~", "")
    d = re.sub(r"-intext:\S+", "", d)
    d = d.replace(" & ", " ")
    d = re.sub(r"\*(\w+)", r"\1", d)
    d = re.sub(r"\bor\s+\w+\s*$", "", d, flags=re.I)
    return re.sub(r"\s+", " ", d).strip()


# ═══════════════════════════════════════════════════════════════════════════
#  URL NORMALIZATION — 100% same
# ═══════════════════════════════════════════════════════════════════════════
_STRIP_PARAMS = frozenset([
    "utm_source","utm_medium","utm_campaign","utm_content","utm_term","utm_id",
    "utm_source_platform","utm_creative_format","utm_marketing_tactic",
    "fbclid","gclid","msclkid","twclid","ttclid","li_fat_id","wbraid",
    "gbraid","dclid","yclid","zanpid","clickid","click_id",
    "msockid","wa","whr","JitExp","mkt","WT.mc_id","WT.srch",
    "__hssc","__hstc","__hsrc","hsctaTracking","hsa_acc","hsa_cam",
    "hsa_grp","hsa_ad","hsa_src","hsa_tgt","hsa_kw","hsa_mt",
    "hsa_net","hsa_ver","mc_cid","mc_eid","vero_id","mkt_tok",
    "ref","referrer","referer","source","share","sid","cid",
    "affiliate","partner","origin","campaign","adid","ad_id",
    "placement","network","device","keyword","matchtype",
    "_ga","_gid","_gl","_gac","ga_source",
    "execution","feedViewType","noredirect","RTN","icid","linkId","adobe_mc",
    "s_kwcid","ef_id",
])


def normalize_url(url: str) -> str:
    try:
        url = url.rstrip("/").strip()
        p = urlparse(url)
        netloc = p.netloc.lower()
        if p.query:
            clean = [
                (k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
                if k.lower() not in _STRIP_PARAMS
            ]
            q = urlencode(sorted(clean)) if clean else ""
        else:
            q = ""
        return f"{p.scheme.lower()}://{netloc}{p.path}" + (f"?{q}" if q else "")
    except Exception:
        return url


def is_valid_url(url: str) -> bool:
    try:
        p = urlparse(url)
        if p.scheme not in ("http", "https"):
            return False
        domain = p.netloc.lower().split(":")[0]
        if domain.startswith("www."):
            domain = domain[4:]
        if not domain or "." not in domain or len(domain) < 4:
            return False
        for bl in BLACKLIST_DOMAINS:
            if domain == bl or domain.endswith("." + bl):
                return False
        if not p.path or p.path in ("/", ""):
            return False
        if JUNK_EXT.search(p.path):
            return False
        if JUNK_URL_PATTERNS.search(url):
            return False
        return True
    except Exception:
        return False


def url_quality_score(url: str) -> int:
    score = 0
    try:
        p = urlparse(url.lower())
        path, query = p.path, p.query
        if query:
            score += 3
            score += min(len(parse_qs(query)), 3)
        if ".php" in path:
            score += 3
            if query:
                score += 3
        elif ".aspx" in path or ".asp" in path:
            score += 2
            if query:
                score += 2
        elif ".cfm" in path or ".jsp" in path:
            score += 1
            if query:
                score += 1
        if HIGH_VALUE.search(path):
            score += 4
        if p.scheme == "https":
            score += 1
    except Exception:
        pass
    return score


# ═══════════════════════════════════════════════════════════════════════════
#  PROXY PICKER — 100% same
# ═══════════════════════════════════════════════════════════════════════════
def _pick_proxy(pool):
    return random.choice(pool) if pool else ""


# ═══════════════════════════════════════════════════════════════════════════
#  CAPTCHA DETECTION — 100% same
# ═══════════════════════════════════════════════════════════════════════════
_CAPTCHA_PHRASES = (
    "captcha", "unusual traffic", "access denied", "robot check",
    "verify you are human", "enable javascript", "checking your browser",
    "just a moment", "ddos protection", "please wait", "security check",
    "bot traffic"
)


def _is_captcha_page(html: str) -> bool:
    sample = html[:3000].lower()
    return any(p in sample for p in _CAPTCHA_PHRASES)


# ═══════════════════════════════════════════════════════════════════════════
#  DDGS SEARCH — 100% same
# ═══════════════════════════════════════════════════════════════════════════
try:
    from ddgs import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    try:
        from duckduckgo_search import DDGS
        DDGS_AVAILABLE = True
    except ImportError:
        DDGS_AVAILABLE = False


def _ddgs_search_sync(dork: str, max_results: int, proxy_list=None):
    if proxy_list is None:
        proxy_list = []
    if not DDGS_AVAILABLE:
        return []
    cleaned = clean_dork_for_search(dork)
    if not cleaned:
        return []
    _ddgs_wait_if_coolingdown()
    for attempt in range(3):
        proxy_url = _pick_proxy(proxy_list)
        try:
            if proxy_url:
                try:
                    ddgs_obj = DDGS(proxy=proxy_url)
                except TypeError:
                    try:
                        ddgs_obj = DDGS(proxies=proxy_url)
                    except Exception:
                        ddgs_obj = DDGS()
            else:
                ddgs_obj = DDGS()
            results = ddgs_obj.text(cleaned, max_results=max_results, safesearch="off")
            urls = []
            for r in (results or []):
                h = r.get("href", "")
                if h and h.startswith("http") and is_valid_url(h):
                    urls.append(h.rstrip("/"))
            if urls:
                _ddgs_record_success()
                return urls
            _ddgs_record_empty()
            time.sleep(0.5 * (attempt + 1))
            _ddgs_wait_if_coolingdown()
        except Exception as ex:
            msg = str(ex).lower()
            if any(k in msg for k in ("ratelimit", "202", "timeout")):
                _ddgs_record_empty()
                time.sleep(1.5 * (attempt + 1))
                _ddgs_wait_if_coolingdown()
            elif attempt < 2:
                time.sleep(0.3)
    _ddgs_record_empty()
    return []


def _ddgs_expand_dork(dork: str, num_variants: int = 3) -> list:
    base = dork.strip()
    has_real_site = bool(re.search(r'site:[a-zA-Z0-9][a-zA-Z0-9.-]{3,}', base))
    if num_variants <= 1 or has_real_site:
        return [base]
    v = [base, base + " site:.com"]
    if num_variants >= 3:
        v.append(base + " site:.org")
    return v


async def search_ddgs_batch(dorks, max_results=12, proxy_list=None, num_variants=3):
    if proxy_list is None:
        proxy_list = []
    if not DDGS_AVAILABLE:
        return []
    expanded = []
    for d in dorks:
        expanded.extend(_ddgs_expand_dork(d, num_variants=num_variants))
    loop = asyncio.get_running_loop()
    all_urls = []
    SUB_BATCH = 20
    for i in range(0, len(expanded), SUB_BATCH):
        sub = expanded[i:i + SUB_BATCH]
        futures = [
            loop.run_in_executor(_THREAD_POOL, _ddgs_search_sync, d, max_results, proxy_list)
            for d in sub
        ]
        results = await asyncio.gather(*futures, return_exceptions=True)
        for r in results:
            if isinstance(r, list):
                all_urls.extend(r)
        if i + SUB_BATCH < len(expanded):
            await asyncio.sleep(0.2)
    return all_urls


# ═══════════════════════════════════════════════════════════════════════════
#  BING REDIRECT DECODE — 100% same
# ═══════════════════════════════════════════════════════════════════════════
def decode_bing_redirect(href: str) -> str:
    try:
        if "bing.com/ck/a" in href or "/ck/a?" in href:
            full = href if href.startswith("http") else "https://www.bing.com" + href
            parsed = urlparse(full)
            params = parse_qs(parsed.query)
            if "u" in params:
                u_val = params["u"][0]
                if u_val.startswith("a1"):
                    u_val = u_val[2:]
                rem = len(u_val) % 4
                if rem:
                    u_val += "=" * (4 - rem)
                decoded = base64.b64decode(u_val).decode("utf-8", errors="ignore")
                if decoded.startswith("http"):
                    return decoded
    except Exception:
        pass
    return href


def _fix_href(href, skip_domain=""):
    if not href:
        return ""
    if "bing.com/ck/a" in href or "/ck/a?" in href:
        href = decode_bing_redirect(href)
    if "uddg=" in href:
        try:
            href = unquote(href.split("uddg=")[1].split("&")[0])
        except Exception:
            pass
    if "/RU=" in href:
        try:
            href = unquote(href.split("/RU=")[1].split("/RK=")[0])
        except Exception:
            pass
    if skip_domain and skip_domain in href.lower():
        return ""
    return href


# ═══════════════════════════════════════════════════════════════════════════
#  EXTRACTORS — 100% same
# ═══════════════════════════════════════════════════════════════════════════
def extract_bing_urls(html: str) -> list:
    urls = []
    try:
        soup = BeautifulSoup(html, "lxml")
        for li in soup.find_all("li", class_="b_algo"):
            for a in li.find_all("a", href=True):
                h = _fix_href(a["href"].strip(), "bing.com")
                if h.startswith("http") and is_valid_url(h):
                    urls.append(h.rstrip("/"))
        for h2 in soup.find_all("h2"):
            a = h2.find("a", href=True)
            if a:
                h = _fix_href(a["href"].strip(), "bing.com")
                if h.startswith("http") and is_valid_url(h):
                    urls.append(h.rstrip("/"))
        if not urls:
            for a in soup.find_all("a", href=True):
                h = _fix_href(a["href"].strip(), "bing.com")
                if h.startswith("http") and is_valid_url(h):
                    urls.append(h.rstrip("/"))
    except Exception:
        pass
    return list(dict.fromkeys(urls))


def extract_ddg_urls(html: str) -> list:
    urls = []
    try:
        soup = BeautifulSoup(html, "lxml")
        for a in soup.find_all("a", href=True):
            h = _fix_href(a["href"].strip(), "duckduckgo.com")
            if h.startswith("http") and is_valid_url(h):
                urls.append(h.rstrip("/"))
    except Exception:
        pass
    return list(dict.fromkeys(urls))


def extract_yandex_urls(html: str) -> list:
    urls = []
    try:
        soup = BeautifulSoup(html, "lxml")
        for a in soup.find_all("a", {"class": lambda c: c and "organic__url" in c}):
            h = _fix_href(a.get("href", "").strip(), "yandex.com")
            if h.startswith("http") and is_valid_url(h):
                urls.append(h.rstrip("/"))
        for tag in soup.find_all(attrs={"data-url": True}):
            h = _fix_href(tag["data-url"].strip(), "yandex.com")
            if h.startswith("http") and is_valid_url(h):
                urls.append(h.rstrip("/"))
        if not urls:
            for a in soup.find_all("a", href=True):
                h = _fix_href(a["href"].strip(), "yandex.com")
                if h.startswith("http") and is_valid_url(h):
                    urls.append(h.rstrip("/"))
    except Exception:
        pass
    return list(dict.fromkeys(urls))


def extract_ask_urls(html: str) -> list:
    urls = []
    try:
        soup = BeautifulSoup(html, "lxml")
        for a in soup.find_all("a", href=True):
            h = _fix_href(a["href"].strip(), "ask.com")
            if h.startswith("http") and is_valid_url(h):
                urls.append(h.rstrip("/"))
    except Exception:
        pass
    return list(dict.fromkeys(urls))


def extract_google_urls(html: str) -> list:
    urls = []
    try:
        soup = BeautifulSoup(html, "lxml")
        for div in soup.find_all("div", class_="yuRUbf"):
            a = div.find("a", href=True)
            if a:
                h = _fix_href(a["href"].strip(), "google.com")
                if h.startswith("http") and is_valid_url(h):
                    urls.append(h.rstrip("/"))
        if not urls:
            for h3 in soup.find_all("h3"):
                a = h3.find_parent("a", href=True)
                if a:
                    h = _fix_href(a["href"].strip(), "google.com")
                    if h.startswith("http") and is_valid_url(h):
                        urls.append(h.rstrip("/"))
    except Exception:
        pass
    return list(dict.fromkeys(urls))


def extract_brave_urls(html: str) -> list:
    urls = []
    try:
        soup = BeautifulSoup(html, "lxml")
        for a in soup.find_all("a", href=True):
            h = _fix_href(a["href"].strip(), "brave.com")
            if h.startswith("http") and is_valid_url(h):
                urls.append(h.rstrip("/"))
    except Exception:
        pass
    return list(dict.fromkeys(urls))


def extract_mojeek_urls(html: str) -> list:
    urls = []
    try:
        soup = BeautifulSoup(html, "lxml")
        for li in soup.find_all("li", class_=re.compile(r"result")):
            a = li.find("a", href=True)
            if a:
                h = _fix_href(a["href"].strip(), "mojeek.com")
                if h.startswith("http") and is_valid_url(h):
                    urls.append(h.rstrip("/"))
        if not urls:
            for a in soup.find_all("a", href=True):
                h = _fix_href(a["href"].strip(), "mojeek.com")
                if h.startswith("http") and is_valid_url(h):
                    urls.append(h.rstrip("/"))
    except Exception:
        pass
    return list(dict.fromkeys(urls))


# ═══════════════════════════════════════════════════════════════════════════
#  SCRAPE ENGINES — 100% same
# ═══════════════════════════════════════════════════════════════════════════
SCRAPE_ENGINES = [
    {"name": "bing",
     "url": "https://www.bing.com/search?q={query}&first={offset}&count=30&setmkt=en-US&setlang=en",
     "extractor": extract_bing_urls,
     "offsets": [1, 11, 21, 31, 41, 51, 61, 71, 81, 91],
     "referer": "https://www.bing.com/", "weight": 5},
    {"name": "google",
     "url": "https://www.google.com/search?q={query}&start={offset}&num=20&hl=en",
     "extractor": extract_google_urls,
     "offsets": [0, 10, 20, 30, 40, 50],
     "referer": "https://www.google.com/", "weight": 3},
    {"name": "brave",
     "url": "https://search.brave.com/search?q={query}&offset={offset}&source=web",
     "extractor": extract_brave_urls,
     "offsets": [0, 10, 20, 30],
     "referer": "https://search.brave.com/", "weight": 2},
    {"name": "ddg_lite",
     "url": "https://lite.duckduckgo.com/lite/?q={query}&s={offset}",
     "extractor": extract_ddg_urls,
     "offsets": [0, 20, 40, 60],
     "referer": "https://lite.duckduckgo.com/", "weight": 2},
    {"name": "ddg_html",
     "url": "https://html.duckduckgo.com/html/?q={query}&s={offset}",
     "extractor": extract_ddg_urls,
     "offsets": [0, 30, 60, 90],
     "referer": "https://html.duckduckgo.com/", "weight": 2},
    {"name": "yandex",
     "url": "https://yandex.com/search/?text={query}&p={offset}",
     "extractor": extract_yandex_urls,
     "offsets": [0, 1, 2, 3],
     "referer": "https://yandex.com/", "weight": 1},
    {"name": "mojeek",
     "url": "https://www.mojeek.com/search?q={query}&s={offset}",
     "extractor": extract_mojeek_urls,
     "offsets": [1, 11, 21, 31],
     "referer": "https://www.mojeek.com/", "weight": 1},
    {"name": "ask",
     "url": "https://www.ask.com/web?q={query}&o={offset}",
     "extractor": extract_ask_urls,
     "offsets": [1, 11, 21, 31],
     "referer": "https://www.ask.com/", "weight": 1},
]

_ENGINE_POOL = [e for e in SCRAPE_ENGINES for _ in range(e.get("weight", 1))]


# ═══════════════════════════════════════════════════════════════════════════
#  FETCH SCRAPE — 100% same
# ═══════════════════════════════════════════════════════════════════════════
async def fetch_scrape(session, engine, dork, offset, semaphore, proxy_list=None):
    if proxy_list is None:
        proxy_list = []
    cleaned = clean_dork_for_search(dork)
    url = engine["url"].format(query=quote_plus(cleaned), offset=offset)
    headers = random.choice(HEADERS_LIST).copy()
    headers["Referer"] = engine.get("referer", "https://www.bing.com/")

    async with semaphore:
        for attempt in range(2):
            try:
                proxy_url = _pick_proxy(proxy_list)
                is_socks = proxy_url.startswith(("socks5://", "socks4://")) if proxy_url else False

                if is_socks:
                    try:
                        from aiohttp_socks import ProxyConnector
                    except ImportError:
                        continue
                    conn = ProxyConnector.from_url(proxy_url, ssl=False)
                    async with aiohttp.ClientSession(connector=conn) as s:
                        async with s.get(url, headers=headers,
                                         timeout=aiohttp.ClientTimeout(total=8),
                                         allow_redirects=True) as r:
                            if r.status == 200:
                                html = await r.text(errors="ignore")
                                if len(html) > 500 and not _is_captcha_page(html):
                                    return engine["extractor"](html)
                    return []

                kw = dict(headers=headers,
                          timeout=aiohttp.ClientTimeout(total=8),
                          ssl=False, allow_redirects=True)
                if proxy_url:
                    kw["proxy"] = proxy_url

                async with session.get(url, **kw) as r:
                    if r.status == 200:
                        html = await r.text(errors="ignore")
                        if len(html) > 500 and not _is_captcha_page(html):
                            return engine["extractor"](html)
                        await asyncio.sleep(0.1 * (attempt + 1))
                        continue
                    elif r.status in (429, 403, 202):
                        await asyncio.sleep(0.5 * (attempt + 1))
                        continue
                    return []
            except asyncio.TimeoutError:
                pass
            except Exception:
                if attempt == 0:
                    await asyncio.sleep(0.05)
        return []


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN FUNCTION — 100% same as bot
# ═══════════════════════════════════════════════════════════════════════════
async def search_urls_from_dorks(dorks, limit=200000, progress_callback=None,
                                  stop_event=None, proxy_list=None):
    """Dorks → URLs via 8 engines + DDGS."""
    if proxy_list is None:
        proxy_list = []
    found = {}
    seen = set()
    domains = {}
    total = len(dorks)
    retries = 0
    last_progress = 0.0
    MAX_PER_DOMAIN = 8
    num_variants = 3 if total <= 500 else (2 if total <= 5000 else 1)
    random.shuffle(dorks)

    def _add(url):
        if len(found) >= limit:
            return
        if not is_valid_url(url):
            return
        n = normalize_url(url)
        if n in seen:
            return
        try:
            d = urlparse(url).netloc.lower().lstrip("www.")
            if domains.get(d, 0) >= MAX_PER_DOMAIN:
                return
            domains[d] = domains.get(d, 0) + 1
        except Exception:
            pass
        seen.add(n)
        found[url.rstrip("/")] = url_quality_score(url)

    async def _report(done):
        nonlocal last_progress
        now = time.monotonic()
        if now - last_progress < 1.5:
            return
        last_progress = now
        if progress_callback:
            try:
                await progress_callback(done, total, len(found), retries)
            except Exception:
                pass

    connector = _get_connector()
    scrape_sem = asyncio.Semaphore(80)
    batch_gate = asyncio.Semaphore(15)

    async def _process_batch(start, batch):
        nonlocal retries
        async with batch_gate:
            if (stop_event and stop_event.is_set()) or len(found) >= limit:
                return
            bing = SCRAPE_ENGINES[0]
            tasks = []
            for d in batch:
                for off in bing["offsets"][:7]:
                    tasks.append(fetch_scrape(session, bing, d, off, scrape_sem, proxy_list))
                sec = random.choice(_ENGINE_POOL)
                tasks.append(fetch_scrape(session, sec, d,
                                          random.choice(sec["offsets"]),
                                          scrape_sem, proxy_list))
            ga = [asyncio.gather(*tasks, return_exceptions=True)]
            if DDGS_AVAILABLE:
                ga.append(asyncio.wait_for(
                    search_ddgs_batch(batch, 100, proxy_list, num_variants),
                    timeout=45.0
                ))
            res = await asyncio.gather(*ga, return_exceptions=True)
            scrape_res = res[0]
            if isinstance(scrape_res, list):
                for r in scrape_res:
                    if isinstance(r, list):
                        for u in r:
                            _add(u)
                    elif isinstance(r, Exception):
                        retries += 1
            if len(res) > 1:
                ddgs_res = res[1]
                if isinstance(ddgs_res, list):
                    for u in ddgs_res:
                        _add(u)
                elif isinstance(ddgs_res, (asyncio.TimeoutError, Exception)):
                    retries += len(batch)
            await _report(min(start + len(batch), total))

    async with aiohttp.ClientSession(connector=connector, connector_owner=False) as session:
        BATCH = 35
        GROUP_SIZE = 90
        starts = list(range(0, total, BATCH))
        for gs in range(0, len(starts), GROUP_SIZE):
            g = starts[gs:gs + GROUP_SIZE]
            await asyncio.gather(
                *[_process_batch(i, dorks[i:i + BATCH]) for i in g],
                return_exceptions=True
            )
            if (stop_event and stop_event.is_set()) or len(found) >= limit:
                break
    return list(dict.fromkeys(
        u for u, _ in sorted(found.items(), key=lambda x: x[1], reverse=True)
    ))