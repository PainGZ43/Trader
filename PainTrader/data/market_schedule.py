from datetime import datetime, time
import asyncio
from core.logger import get_logger

class MarketSchedule:
    """
    Manages Market Hours (09:00 ~ 15:30).
    """
    def __init__(self):
        self.logger = get_logger("MarketSchedule")
        self.market_open_time = time(9, 0)
        self.market_close_time = time(15, 30)
        self.is_market_open = False

    def check_market_status(self):
        """
        Check if current time is within market hours.
        """
        now = datetime.now().time()
        if self.market_open_time <= now <= self.market_close_time:
            if not self.is_market_open:
                self.logger.info("Market is OPEN")
                self.is_market_open = True
            return True
        else:
            if self.is_market_open:
                self.logger.info("Market is CLOSED")
                self.is_market_open = False
            return False

    async def wait_for_market_open(self):
        """
        Block until market opens.
        """
        while not self.check_market_status():
            await asyncio.sleep(60) # Check every minute

market_schedule = MarketSchedule()
