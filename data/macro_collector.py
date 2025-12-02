import asyncio
import aiohttp
from core.logger import get_logger
from data.kiwoom_rest_client import kiwoom_client
from core.event_bus import event_bus
from data.websocket_client import ws_client

class MacroCollector:
    """
    Collects Macroeconomic Data:
    - Market Indices (KOSPI)
    - Exchange Rates (USD/KRW)
    """
    def __init__(self):
        self.logger = get_logger("MacroCollector")
        self.rest_client = kiwoom_client
        self.ws_client = ws_client
        self.indices = {
            "KOSPI": 0.0
        }
        self.changes = {} 
        self.exchange_rate = 0.0

    async def subscribe_indices(self):
        """
        Subscribe to Real-time Index Data (JISU).
        """
        self.logger.info("Subscribing to Real-time Indices...")
        # KOSPI (001)
        await self.ws_client.subscribe("JISU", "001")

    async def update_market_indices(self):
        """
        Fetch KOSPI index via Kiwoom API.
        """
        try:
            # Fetch KOSPI (001)
            kospi_data = await self.rest_client.get_market_index("001") 
            
            if kospi_data:
                price = 0.0
                # Check for PDF structure (inds_netprps)
                if "inds_netprps" in kospi_data:
                    items = kospi_data["inds_netprps"]
                    if items:
                        # cur_prc might be string like "+2500.50" or "2500.50"
                        price_str = items[0].get("cur_prc", "0")
                        price = float(price_str.replace(",", "").replace("+", ""))
                
                # Fallback to old structure (output.price) if needed
                elif "output" in kospi_data:
                    price = float(str(kospi_data.get("output", {}).get("price", "0")).replace(",", ""))
                
                if price > 0:
                    self.indices["KOSPI"] = price
                
            self.logger.info(f"Updated Local Indices: KOSPI={self.indices['KOSPI']}")
            
        except Exception as e:
            self.logger.error(f"Failed to update local indices: {e}")

    async def update_exchange_rate(self):
        """
        Fetch USD/KRW exchange rate using KODEX USD Futures (261240) as proxy.
        ETF Price ~= Exchange Rate * 10
        """
        try:
            # KODEX USD Futures (261240)
            data = await self.rest_client.get_current_price("261240")
            
            if data and "output" in data:
                price_str = data["output"].get("price", "0")
                price = float(price_str.replace(",", ""))
                
                # Calculate Rate (Approximate)
                if price > 0:
                    self.exchange_rate = price / 10.0
                    self.logger.info(f"Updated USD/KRW (via Kiwoom): {self.exchange_rate} (ETF: {price})")
                else:
                    self.logger.warning("Kiwoom returned 0 price for USD Futures ETF")
            else:
                self.logger.warning("Failed to fetch USD Futures ETF from Kiwoom")
                
        except Exception as e:
            self.logger.error(f"Exchange rate update error: {e}")

    async def on_realtime_data(self, data):
        """
        Handle Real-time Data from WebSocket.
        """
        msg_type = data.get("type")
        if msg_type == "JISU":
            code = data.get("code")
            price = float(data.get("price", 0))
            change_pct = data.get("change_pct", "0.0%")
            
            name = None
            if code == "001":
                name = "KOSPI"
            
            if name:
                self.indices[name] = price
                self.changes[name] = change_pct
                
                # Publish Event Immediately
                event_data = {
                    "indices": self.indices,
                    "changes": self.changes,
                    "exchange_rate": self.exchange_rate
                }
                event_bus.publish("market.data.macro", event_data)

    async def start_scheduler(self):
        """
        Periodically update macro data.
        """
        self.logger.info("Starting MacroCollector Scheduler...")
        
        # Initial Subscription
        await self.subscribe_indices()
        
        while True:
            await self.update_market_indices()
            await self.update_exchange_rate()
            
            # Publish Event (Periodic)
            event_data = {
                "indices": self.indices,
                "changes": self.changes,
                "exchange_rate": self.exchange_rate
            }
            event_bus.publish("market.data.macro", event_data)
            
            await asyncio.sleep(10) # 10s polling for backup

macro_collector = MacroCollector()
