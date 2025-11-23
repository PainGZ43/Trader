import asyncio
import aiohttp
from core.logger import get_logger
from data.kiwoom_rest_client import kiwoom_client

class MacroCollector:
    """
    Collects Macroeconomic Data:
    - Market Indices (KOSPI, KOSDAQ)
    - Exchange Rates (USD/KRW)
    """
    def __init__(self):
        self.logger = get_logger("MacroCollector")
        self.rest_client = kiwoom_client
        self.indices = {"KOSPI": 0.0, "KOSDAQ": 0.0}
        self.exchange_rate = 0.0

    async def update_market_indices(self):
        """
        Fetch KOSPI/KOSDAQ indices via Kiwoom API.
        """
        try:
            # Example: Fetching KOSPI (001) and KOSDAQ (101)
            # In real Kiwoom API, this might be a specific TR code like OPT20001 or OPT20006
            # Here we assume a REST endpoint exists or we mock it.
            
            # Placeholder logic
            kospi_data = await self.rest_client.get_current_price("001") # 001 is often KOSPI
            kosdaq_data = await self.rest_client.get_current_price("101") # 101 is often KOSDAQ
            
            if kospi_data:
                self.indices["KOSPI"] = float(kospi_data.get("output", {}).get("price", 2500.0))
            if kosdaq_data:
                self.indices["KOSDAQ"] = float(kosdaq_data.get("output", {}).get("price", 850.0))
                
            self.logger.info(f"Updated Indices: {self.indices}")
            
        except Exception as e:
            self.logger.error(f"Failed to update indices: {e}")

    async def update_exchange_rate(self):
        """
        Fetch USD/KRW exchange rate.
        Uses a public API or Kiwoom if available.
        """
        url = "https://api.exchangerate-api.com/v4/latest/USD" # Free public API example
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.exchange_rate = data.get("rates", {}).get("KRW", 1300.0)
                        self.logger.info(f"Updated USD/KRW: {self.exchange_rate}")
                    else:
                        self.logger.warning("Failed to fetch exchange rate from external API")
        except Exception as e:
            self.logger.error(f"Exchange rate update error: {e}")

    async def start_scheduler(self):
        """
        Periodically update macro data.
        """
        self.logger.info("Starting MacroCollector Scheduler...")
        while True:
            await self.update_market_indices()
            await self.update_exchange_rate()
            await asyncio.sleep(60) # Update every minute

macro_collector = MacroCollector()
