import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from collections import deque
from core.logger import get_logger
from core.config import config

class NotificationManager:
    """
    Manages system notifications via KakaoTalk and Logging.
    Features:
    - Rate Limiting (e.g., 1 message per second)
    - Duplicate Prevention (debounce)
    - Automatic Token Refresh
    """
    def __init__(self):
        self.logger = get_logger("NotificationManager")
        
        # Config
        from core.secure_storage import secure_storage
        
        # Load from SecureStorage (Priority) or Config (Fallback)
        self.kakao_app_key = secure_storage.get("kakao_app_key") or config.get("KAKAO_APP_KEY")
        self.kakao_token = secure_storage.get("kakao_access_token") or config.get("KAKAO_ACCESS_TOKEN")
        self.refresh_token = secure_storage.get("kakao_refresh_token") or config.get("KAKAO_REFRESH_TOKEN")
        
        self.enabled = bool(self.kakao_token)
        self.notify_level = config.get("NOTIFY_LEVEL", "ALL") # ALL, ERROR_ONLY, NONE
        
        # Rate Limiting
        self.queue = asyncio.Queue()
        self.rate_limit_delay = 1.0 # Seconds between messages
        self._running = False
        self._worker_task = None
        
        # Duplicate Prevention
        self.recent_messages = {} # hash -> timestamp
        self.duplicate_window = 60 # Seconds
        
        if not self.enabled:
            self.logger.warning("Kakao Token not found. Notifications disabled.")

    async def start(self):
        """Start background worker."""
        if self.enabled and not self._running:
            self._running = True
            self._worker_task = asyncio.create_task(self._process_queue())
            self.logger.info("Notification Manager Started")
            # Send startup message
            await self.send_message("🤖 [시스템] 트레이딩 서버 시작", level="INFO")

    async def wait_all_sent(self):
        """Wait until all queued messages are processed."""
        if self._running:
            await self.queue.join()

    async def stop(self):
        """Stop background worker."""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Notification Manager Stopped")

    async def send_message(self, message: str, level: str = "INFO"):
        """
        Enqueue message for sending.
        level: INFO, WARNING, ERROR
        """
        # Always log first
        if level == "ERROR":
            self.logger.error(message)
        elif level == "WARNING":
            self.logger.warning(message)
        else:
            self.logger.info(f"[NOTI] {message}")
            
        if not self.enabled:
            return

        # Level Filter
        if self.notify_level == "NONE":
            return
        if self.notify_level == "ERROR_ONLY" and level not in ["ERROR", "WARNING"]:
            return

        # Duplicate Check
        msg_hash = hash(message)
        now = datetime.now().timestamp()
        if msg_hash in self.recent_messages:
            last_time = self.recent_messages[msg_hash]
            if now - last_time < self.duplicate_window:
                self.logger.debug(f"Duplicate notification suppressed: {message[:20]}...")
                return
        
        self.recent_messages[msg_hash] = now
        
        # Clean up old hashes periodically (simple way: random chance or fixed size)
        if len(self.recent_messages) > 100:
            self.recent_messages.clear() # Simple clear to prevent leak

        await self.queue.put(message)

    async def send_daily_report(self, summary: Dict[str, Any]):
        """
        Format and send daily report.
        summary: from AccountManager.get_summary()
        """
        balance = summary.get("balance", {})
        total_asset = balance.get("total_asset", 0)
        daily_pnl = balance.get("daily_pnl", 0)
        positions = summary.get("positions", {})
        
        pnl_rate = 0.0
        if total_asset > 0:
            pnl_rate = (daily_pnl / total_asset) * 100
            
        msg = (
            f"📅 [일일 리포트] {datetime.now().strftime('%Y-%m-%d')}\n"
            f"총자산: {total_asset:,.0f}원\n"
            f"당일손익: {daily_pnl:+,.0f}원 ({pnl_rate:+.2f}%)\n"
            f"보유종목: {len(positions)}개"
        )
        await self.send_message(msg, level="INFO")

    async def _process_queue(self):
        """Background worker to send messages with rate limiting."""
        while self._running:
            try:
                message = await self.queue.get()
                await self._send_kakao(message)
                self.queue.task_done()
                await asyncio.sleep(self.rate_limit_delay)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Notification Worker Error: {e}")

    async def _send_kakao(self, message: str):
        """Send actual HTTP request to Kakao API."""
        url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
        headers = {
            "Authorization": f"Bearer {self.kakao_token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        # Template: Text
        payload = {
            "template_object": json.dumps({
                "object_type": "text",
                "text": message,
                "link": {
                    "web_url": "https://www.kakao.com",
                    "mobile_web_url": "https://www.kakao.com"
                }
            })
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, headers=headers, data=payload) as resp:
                    if resp.status == 200:
                        self.logger.debug("Kakao Message Sent")
                    elif resp.status == 401: # Unauthorized (Token Expired)
                        self.logger.warning("Kakao Token Expired. Refreshing...")
                        if await self._refresh_token_api():
                            # Retry once
                            headers["Authorization"] = f"Bearer {self.kakao_token}"
                            async with session.post(url, headers=headers, data=payload) as retry_resp:
                                if retry_resp.status == 200:
                                    self.logger.info("Kakao Message Sent (After Refresh)")
                                else:
                                    self.logger.error(f"Kakao Send Failed (Retry): {retry_resp.status}")
                    else:
                        text = await resp.text()
                        self.logger.error(f"Kakao Send Failed: {resp.status} - {text}")
            except Exception as e:
                self.logger.error(f"Kakao Connection Error: {e}")

    async def _refresh_token_api(self) -> bool:
        """Refresh Kakao Access Token."""
        if not self.refresh_token:
            self.logger.error("No Refresh Token available.")
            return False
            
        url = "https://kauth.kakao.com/oauth/token"
        data = {
            "grant_type": "refresh_token",
            "client_id": self.kakao_app_key, # Use loaded key
            "refresh_token": self.refresh_token
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, data=data) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        self.kakao_token = result.get("access_token")
                        
                        # Save to SecureStorage
                        from core.secure_storage import secure_storage
                        secure_storage.save("kakao_access_token", self.kakao_token)
                        
                        if "refresh_token" in result:
                            self.refresh_token = result.get("refresh_token")
                            secure_storage.save("kakao_refresh_token", self.refresh_token)
                        
                        self.logger.info("Kakao Token Refreshed Successfully")
                        return True
                    else:
                        self.logger.error(f"Token Refresh Failed: {await resp.text()}")
                        return False
            except Exception as e:
                self.logger.error(f"Token Refresh Error: {e}")
                return False
