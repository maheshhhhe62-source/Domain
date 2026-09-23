"""
Spidey Core — Proxy Manager (CLEAN v3.0)
- No duplicate functions
- Fast live check (5s timeout, HTTP)
- SOCKS + HTTP support
- Web storage + manual input
"""
import os
import io
import json
import time
import random
import zipfile
import asyncio
import logging

import aiohttp

try:
    from aiohttp_socks import ProxyConnector as _ProxyConnector
    _SOCKS_AVAILABLE = True
except ImportError:
    _SOCKS_AVAILABLE = False

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
#  STORAGE PATH
# ═══════════════════════════════════════════════════════════════════════════
DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data"
)
os.makedirs(DATA_DIR, exist_ok=True)
PROXY_FILE = os.path.join(DATA_DIR, "proxies.json")


# ═══════════════════════════════════════════════════════════════════════════
#  CAPTCHA DETECTION
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
#  PARSE PROXY
# ═══════════════════════════════════════════════════════════════════════════
def parse_proxy(proxy_str: str) -> str:
    """
    Formats:
      1.2.3.4:8080                → socks5://1.2.3.4:8080
      1.2.3.4:8080:user:pass      → http://user:pass@1.2.3.4:8080
      user:pass@1.2.3.4:8080      → http://user:pass@1.2.3.4:8080
      http://1.2.3.4:8080         → as-is
      socks5://1.2.3.4:8080       → as-is
    """
    if not proxy_str:
        return ""
    s = proxy_str.strip().rstrip("\r")
    if not s:
        return ""

    # Already has scheme
    if s.startswith(("http://", "https://", "socks5://", "socks4://")):
        return s

    # user:pass@host:port
    if "@" in s and ":" in s:
        try:
            up, hp = s.split("@", 1)
            u, p = up.split(":", 1)
            return f"http://{u}:{p}@{hp}"
        except Exception:
            pass

    parts = s.split(":")
    # host:port:user:pass
    if len(parts) == 4:
        h, p, u, pw = parts
        return f"http://{u}:{pw}@{h}:{p}"

    # host:port → default to socks5
    if len(parts) == 2:
        return f"socks5://{s}"

    return f"socks5://{s}"


def parse_proxy_text(text: str) -> list:
    """
    Multi-line text → list of unique proxies.
    Skips lines starting with #, ;, [
    """
    out, seen = [], set()
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith(("#", ";", "[")):
            continue
        if "=" in line and not line.startswith("http"):
            continue
        if ":" not in line:
            continue
        pp = parse_proxy(line)
        if pp and pp not in seen:
            seen.add(pp)
            out.append(pp)
    return out


def parse_proxy_from_zip(zip_bytes: bytes) -> list:
    """Extract proxies from ZIP file bytes"""
    out, seen = [], set()
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            for n in zf.namelist():
                if n.startswith("__"):
                    continue
                if not n.lower().endswith((".txt", ".text", ".dat")):
                    continue
                try:
                    with zf.open(n) as f:
                        text = f.read().decode("utf-8", errors="ignore")
                    for p in parse_proxy_text(text):
                        if p not in seen:
                            seen.add(p)
                            out.append(p)
                except Exception:
                    pass
    except Exception as e:
        logger.error(f"[proxy] zip error: {e}")
    return out


# ═══════════════════════════════════════════════════════════════════════════
#  STORAGE — per user
# ═══════════════════════════════════════════════════════════════════════════
def load_all() -> dict:
    try:
        with open(PROXY_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
            if not isinstance(d, dict):
                return {"admin": []}
            return d
    except Exception:
        return {"admin": []}


def save_all(d: dict):
    try:
        with open(PROXY_FILE, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=2)
    except Exception as e:
        logger.error(f"[proxy] save error: {e}")


def get_proxies(uid: str = "admin") -> list:
    d = load_all()
    return d.get(uid, [])


def set_proxies(uid: str, lst: list):
    d = load_all()
    d[uid] = list(dict.fromkeys(lst))
    save_all(d)


def add_proxies(uid: str, new_list: list) -> dict:
    d = load_all()
    cur = d.get(uid, [])
    seen = set(cur)
    added, dup = 0, 0
    for p in new_list:
        if p in seen:
            dup += 1
        else:
            seen.add(p)
            cur.append(p)
            added += 1
    d[uid] = cur
    save_all(d)
    return {"added": added, "dup": dup, "total": len(cur)}


def remove_proxies(uid: str, kill_list: list) -> int:
    d = load_all()
    cur = d.get(uid, [])
    new = [p for p in cur if p not in kill_list]
    removed = len(cur) - len(new)
    d[uid] = new
    save_all(d)
    return removed


def clear_proxies(uid: str = "admin") -> int:
    d = load_all()
    n = len(d.get(uid, []))
    d[uid] = []
    save_all(d)
    return n


# ═══════════════════════════════════════════════════════════════════════════
#  🚀 FAST PROXY LIVE CHECK — 5s timeout, HTTP (single function, no duplicate)
# ═══════════════════════════════════════════════════════════════════════════
async def check_proxy_live(proxy_url: str, timeout: float = 5.0) -> bool:
    """
    🚀 Fast proxy check:
    - 5s timeout (not 8s)
    - HTTP test (not HTTPS — faster)
    - Returns True if status in (200, 301, 302, 403)
    """
    if not proxy_url:
        return False
    
    is_socks = proxy_url.startswith(("socks5://", "socks4://"))
    test_url = "http://httpbin.org/ip"
    
    try:
        if is_socks and _SOCKS_AVAILABLE:
            connector = _ProxyConnector.from_url(proxy_url, ssl=False)
            async with aiohttp.ClientSession(connector=connector) as s:
                async with s.get(
                    test_url,
                    timeout=aiohttp.ClientTimeout(total=timeout, connect=3),
                    allow_redirects=False,
                ) as r:
                    return r.status in (200, 301, 302, 403)
        else:
            kw = dict(
                timeout=aiohttp.ClientTimeout(total=timeout, connect=3),
                allow_redirects=False,
            )
            if not is_socks:
                kw["proxy"] = proxy_url
            async with aiohttp.ClientSession() as s:
                async with s.get(test_url, **kw) as r:
                    return r.status in (200, 301, 302, 403)
    except asyncio.TimeoutError:
        return False
    except aiohttp.ClientError:
        return False
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════════════════════
#  🚀 BULK PROXY CHECK — Parallel, no hang
# ═══════════════════════════════════════════════════════════════════════════
async def check_proxies_bulk(
    proxy_list,
    timeout: float = 5.0,
    concurrency: int = 300,
    progress_callback=None,
    task_id: str = None,
) -> list:
    """
    🚀 Check list of proxies in parallel.
    
    - timeout: 5s per proxy
    - concurrency: 300 (parallel)
    - progress_callback(checked, total, live) — called ~every 1s
    - task_id: optional, for cancel support
    
    Returns: list of LIVE proxies
    """
    if not proxy_list:
        return []
    
    total = len(proxy_list)
    live = []
    checked = 0
    last_report = [time.time()]
    sem = asyncio.Semaphore(concurrency)

    async def _check(px):
        nonlocal checked, live
        # Cancel check
        if task_id:
            try:
                from web.main import is_cancelled
                if is_cancelled(task_id):
                    return
            except Exception:
                pass
        
        async with sem:
            try:
                is_live = await check_proxy_live(px, timeout=timeout)
            except Exception:
                is_live = False
            
            if is_live:
                live.append(px)
            checked += 1
            
            # Progress callback (throttled ~1s)
            now = time.time()
            if progress_callback and (now - last_report[0]) >= 1.0:
                last_report[0] = now
                try:
                    result = progress_callback(checked, total, len(live))
                    if asyncio.iscoroutine(result):
                        await result
                except Exception:
                    pass

    # ✅ Run ALL in parallel (no batching — 300 concurrency is enough)
    await asyncio.gather(*[_check(p) for p in proxy_list], return_exceptions=True)

    # Final callback
    if progress_callback:
        try:
            result = progress_callback(checked, total, len(live))
            if asyncio.iscoroutine(result):
                await result
        except Exception:
            pass
    
    return live


# ═══════════════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════════════
def pick_random(uid: str = "admin") -> str:
    pool = get_proxies(uid)
    return random.choice(pool) if pool else ""


def pick_pool(uid: str = "admin", global_pool: list = None) -> list:
    user_pool = get_proxies(uid)
    if user_pool:
        return user_pool
    return global_pool or []


def proxy_stats(uid: str = "admin") -> dict:
    pool = get_proxies(uid)
    socks = sum(1 for p in pool if p.startswith(("socks5://", "socks4://")))
    http = len(pool) - socks
    return {"total": len(pool), "socks": socks, "http": http}


def _format_proxy_for_aiohttp(proxy: str) -> str:
    """Format proxy for aiohttp `proxy=` param"""
    if not proxy:
        return ""
    p = proxy.strip()
    if p.startswith(("http://", "https://")):
        return p
    if p.startswith(("socks5://", "socks4://")):
        return p  # aiohttp doesn't support socks directly
    # ip:port format
    parts = p.split(":")
    if len(parts) == 2:
        return f"http://{parts[0]}:{parts[1]}"
    elif len(parts) == 4:
        return f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
    return f"http://{p}"


# ═══════════════════════════════════════════════════════════════════════════
#  ASYNC FETCH WRAPPER — for url_finder / sqli
# ═══════════════════════════════════════════════════════════════════════════
async def fetch_with_proxy(
    proxy_url: str,
    url: str,
    headers: dict = None,
    timeout: float = 8.0,
) -> str:
    """
    Fetch URL via proxy. Returns HTML or "" on failure.
    """
    if not proxy_url:
        # Direct fetch (no proxy)
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(
                    url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                    ssl=False,
                    allow_redirects=True,
                ) as r:
                    if r.status == 200:
                        html = await r.text(errors="ignore")
                        if len(html) > 500 and not _is_captcha_page(html):
                            return html
        except Exception:
            pass
        return ""

    is_socks = proxy_url.startswith(("socks5://", "socks4://"))

    # SOCKS via separate connector
    if is_socks and _SOCKS_AVAILABLE:
        try:
            conn = _ProxyConnector.from_url(proxy_url, ssl=False)
            async with aiohttp.ClientSession(connector=conn) as s:
                async with s.get(
                    url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                    ssl=False,
                    allow_redirects=True,
                ) as r:
                    if r.status == 200:
                        html = await r.text(errors="ignore")
                        if len(html) > 500 and not _is_captcha_page(html):
                            return html
        except Exception:
            pass
        return ""

    # HTTP / HTTPS proxy
    try:
        kw = dict(
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=timeout),
            ssl=False,
            allow_redirects=True,
            proxy=proxy_url,
        )
        async with aiohttp.ClientSession() as s:
            async with s.get(url, **kw) as r:
                if r.status == 200:
                    html = await r.text(errors="ignore")
                    if len(html) > 500 and not _is_captcha_page(html):
                        return html
    except Exception:
        pass
    return ""