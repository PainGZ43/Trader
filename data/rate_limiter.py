import asyncio
import time
from core.logger import get_logger

class RateLimiter:
    """
    Token Bucket implementation for API rate limiting.
    """
    def __init__(self, max_tokens, refill_rate):
        """
        :param max_tokens: Maximum burst size (bucket capacity).
        :param refill_rate: Tokens added per second.
        """
        self.max_tokens = max_tokens
        self.tokens = max_tokens
        self.refill_rate = refill_rate
        self.last_refill = time.monotonic()
        self.logger = get_logger("RateLimiter")
        self._lock = asyncio.Lock()

    async def acquire(self, tokens=1):
        """
        Wait until enough tokens are available.
        """
        async with self._lock:
            while True:
                self._refill()
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return
                
                # Wait for enough tokens to accumulate
                needed = tokens - self.tokens
                wait_time = needed / self.refill_rate
                await asyncio.sleep(wait_time)

    def _refill(self):
        now = time.monotonic()
        elapsed = now - self.last_refill
        new_tokens = elapsed * self.refill_rate
        
        if new_tokens > 0:
            self.tokens = min(self.max_tokens, self.tokens + new_tokens)
            self.last_refill = now
