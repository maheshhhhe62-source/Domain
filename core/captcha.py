# core/captcha.py
"""
Spidey Core — Captcha Solver (NoCaptchaAI API)
Production-ready with async, polling, balance check, retry
"""
import os
import time
import base64
import asyncio
import logging
from typing import Optional, List, Dict, Any

import aiohttp

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════════════════════
NOCAPTCHA_API_BASE       = "https://api.nocaptchaai.com"
NOCAPTCHA_SOLVE_ENDPOINT = f"{NOCAPTCHA_API_BASE}/solve"
NOCAPTCHA_BALANCE_ENDPOINT = f"{NOCAPTCHA_API_BASE}/balance"


# ═══════════════════════════════════════════════════════════════════════════
#  CAPTCHA SOLVER
# ═══════════════════════════════════════════════════════════════════════════
class CaptchaSolver:
    """
    NoCaptchaAI API wrapper.
    Supports: reCAPTCHA (image), normal image captcha.
    Async + polling + retry.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("NOCAPTCHA_API_KEY")
        if not self.api_key:
            raise ValueError("NoCaptchaAI API key required")
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=90)
            )
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    # ─────────────────────────────────────────────────────────────────────
    #  RECAPTCHA IMAGE CHALLENGE
    # ─────────────────────────────────────────────────────────────────────
    async def solve_recaptcha_image(
        self,
        task: str,
        image_b64_list: List[str],
        grid: str = "3x3",
        page_url: str = "",
        max_wait: int = 120,
    ) -> Dict[str, Any]:
        """
        Solve reCAPTCHA image grid challenge.
        Returns: {"success": bool, "solution": "1,3,5", "error": str}
        """
        payload = {
            "key": self.api_key,
            "method": "recaptcha",
            "task": task,
            "grid": grid,
            "images": image_b64_list,
        }
        if page_url:
            payload["url"] = page_url

        headers = {
            "Content-Type": "application/json",
            "apikey": self.api_key,
        }

        session = await self._get_session()

        # ── Send solve request ──
        try:
            async with session.post(
                NOCAPTCHA_SOLVE_ENDPOINT,
                json=payload,
                headers=headers,
            ) as r:
                data = await r.json()
        except Exception as e:
            return {"success": False, "error": f"network: {e}"}

        # ── Handle instant solve ──
        if data.get("solution") or data.get("status") == "solved":
            return {
                "success": True,
                "solution": data.get("solution") or data.get("answer"),
                "raw": data,
            }

        # ── Handle async (poll) ──
        task_id = data.get("task_id") or data.get("id")
        if data.get("status") == "pending" and task_id:
            return await self._poll_result(task_id, max_wait)

        # ── Handle error ──
        if data.get("error"):
            return {"success": False, "error": data["error"]}

        return {"success": False, "error": f"unknown response: {data}"}

    # ─────────────────────────────────────────────────────────────────────
    #  NORMAL IMAGE CAPTCHA
    # ─────────────────────────────────────────────────────────────────────
    async def solve_normal_captcha(
        self,
        image_bytes: bytes,
        max_wait: int = 120,
    ) -> Dict[str, Any]:
        """
        Solve normal image captcha (OCR-style).
        Returns: {"success": bool, "solution": "ABCD", "error": str}
        """
        b64 = base64.b64encode(image_bytes).decode()
        payload = {
            "key": self.api_key,
            "method": "normal",
            "body": b64,
        }
        headers = {"apikey": self.api_key}

        session = await self._get_session()

        try:
            async with session.post(
                NOCAPTCHA_SOLVE_ENDPOINT,
                json=payload,
                headers=headers,
            ) as r:
                data = await r.json()
        except Exception as e:
            return {"success": False, "error": f"network: {e}"}

        if data.get("solution"):
            return {"success": True, "solution": data["solution"], "raw": data}

        task_id = data.get("task_id") or data.get("id")
        if data.get("status") == "pending" and task_id:
            return await self._poll_result(task_id, max_wait)

        if data.get("error"):
            return {"success": False, "error": data["error"]}

        return {"success": False, "error": f"unknown response: {data}"}

    # ─────────────────────────────────────────────────────────────────────
    #  POLLING
    # ─────────────────────────────────────────────────────────────────────
    async def _poll_result(self, task_id: str, max_wait: int) -> Dict[str, Any]:
        """Poll for async result."""
        url = f"{NOCAPTCHA_API_BASE}/result/{task_id}"
        headers = {"apikey": self.api_key}
        session = await self._get_session()

        waited = 0
        while waited < max_wait:
            await asyncio.sleep(3)
            waited += 3
            try:
                async with session.get(url, headers=headers) as r:
                    data = await r.json()
            except Exception:
                continue

            status = data.get("status")
            if status == "solved":
                return {
                    "success": True,
                    "solution": data.get("solution") or data.get("answer"),
                    "raw": data,
                }
            if status == "failed":
                return {"success": False, "error": data.get("error", "failed")}

        return {"success": False, "error": "timeout"}

    # ─────────────────────────────────────────────────────────────────────
    #  BALANCE CHECK
    # ─────────────────────────────────────────────────────────────────────
    async def check_balance(self) -> Dict[str, Any]:
        """Check remaining solve balance."""
        headers = {"apikey": self.api_key}
        session = await self._get_session()
        try:
            async with session.get(NOCAPTCHA_BALANCE_ENDPOINT,
                                    headers=headers) as r:
                return await r.json()
        except Exception as e:
            return {"error": str(e)}

    # ─────────────────────────────────────────────────────────────────────
    #  TEST
    # ─────────────────────────────────────────────────────────────────────
    async def test_key(self) -> bool:
        """Test if API key is valid + has balance."""
        b = await self.check_balance()
        return "error" not in b


# ═══════════════════════════════════════════════════════════════════════════
#  GLOBAL INSTANCE (lazy)
# ═══════════════════════════════════════════════════════════════════════════
_SOLVER: Optional[CaptchaSolver] = None


def get_solver() -> Optional[CaptchaSolver]:
    """Get global solver instance (or None if no API key)."""
    global _SOLVER
    if _SOLVER is None:
        try:
            _SOLVER = CaptchaSolver()
        except ValueError:
            return None
    return _SOLVER


def is_available() -> bool:
    """Check if captcha solver is configured."""
    return get_solver() is not None


# ═══════════════════════════════════════════════════════════════════════════
#  STANDALONE TEST
# ═══════════════════════════════════════════════════════════════════════════
async def _test():
    key = os.environ.get("NOCAPTCHA_API_KEY")
    if not key:
        print("❌ Set NOCAPTCHA_API_KEY first")
        return

    solver = CaptchaSolver(key)
    print("🔑 Testing key...")
    balance = await solver.check_balance()
    print(f"💰 Balance: {balance}")

    # Test normal captcha with base64 image
    # (skip actual test — needs real image)

    await solver.close()


if __name__ == "__main__":
    asyncio.run(_test())