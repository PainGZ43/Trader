from datetime import datetime, time
import asyncio
import holidays
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
        self.kr_holidays = holidays.KR()

    def check_market_status(self):
        """
        Check if current time is within market hours.
        """
        if not self.is_business_day():
            if self.is_market_open:
                self.logger.info("Market is CLOSED (Holiday/Weekend)")
                self.is_market_open = False
            return False

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

    def is_business_day(self):
        """
        Check if today is a business day (Mon-Fri) and not a public holiday.
        """
        now = datetime.now()
        today = now.weekday()
        date_str = now.strftime("%Y-%m-%d")
        
        # 1. Weekend Check
        if today >= 5: # 5=Sat, 6=Sun
            return False
            
        # 2. Holiday Check
        if date_str in self.kr_holidays:
            self.logger.info(f"Today is a holiday: {self.kr_holidays.get(date_str)}")
            return False
            
        return True

    async def wait_for_market_open(self):
        """
        Block until market opens.
        """
        while not self.check_market_status():
            await asyncio.sleep(60) # Check every minute

market_schedule = MarketSchedule()
