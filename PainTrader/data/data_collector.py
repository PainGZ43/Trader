import asyncio
import pandas as pd
from datetime import datetime
from core.database import db
from data.market_schedule import market_schedule
from core.logger import get_logger
from data.kiwoom_rest_client import kiwoom_client
from data.websocket_client import ws_client
from data.macro_collector import macro_collector

class DataCollector:
    """
    Central Data Management Unit.
    - Collects real-time data from WebSocket.
    - Collects historical data from REST API.
    - Handles Gap Filling (Network reconnection).
    - Buffers data and saves to Database.
    - Manages Macro Data.
    """
    def __init__(self):
        self.logger = get_logger("DataCollector")
        self.rest_client = kiwoom_client
        self.ws_client = ws_client
        self.market_schedule = market_schedule
        self.macro_collector = macro_collector
        
        # Data Buffer: {symbol: DataFrame}
        self.realtime_buffer = {} 
        
        # Last update time for Gap Filling
        self.last_update_time = {} 
        
        # UI Observers
        self.observers = []

        # Register callback
        self.ws_client.add_callback(self.on_realtime_data)

    def add_observer(self, callback):
        """
        Add UI observer callback.
        """
        self.observers.append(callback)

    async def start(self):
        """
        Start data collection services.
        """
        self.logger.info("Starting DataCollector...")
        await db.connect()
        await self.sync_symbol_master()
        await self.ws_client.connect()
        
        # Start background tasks
        asyncio.create_task(self._schedule_monitor())
        asyncio.create_task(self._macro_monitor())

    async def stop(self):
        """
        Stop data collection services.
        """
        self.logger.info("Stopping DataCollector...")
        await self.ws_client.disconnect()
        await self.rest_client.close()
        await db.close()

    async def on_realtime_data(self, data):
        """
        Callback for WebSocket data.
        """
        try:
            # Check Market Hours
            if not self.market_schedule.check_market_status():
                return

            symbol = data.get("code")
            price = data.get("price")
            timestamp = datetime.now() # Or use server timestamp if available
            
            if not symbol:
                return

            # Update Buffer & Save to DB
            self.logger.debug(f"Realtime Data: {symbol} - {price}")
            await self.save_to_db(symbol, timestamp, price, data.get("volume", 0))
            
            # Update Buffer & Save to DB
            self.logger.debug(f"Realtime Data: {symbol} - {price}")
            await self.save_to_db(symbol, timestamp, price, data.get("volume", 0))
            
            # Notify Observers (UI)
            data['type'] = 'REALTIME'
            await self.notify_observers(data)
            
            # Gap Filling Check
            
            # Gap Filling Check
            last_time = self.last_update_time.get(symbol)
            if last_time:
                time_diff = (timestamp - last_time).total_seconds()
                if time_diff > 60: # If no data for 60s, assume gap
                    self.logger.warning(f"Gap detected for {symbol} ({time_diff}s). Triggering Gap Filling...")
                    asyncio.create_task(self.fill_gap(symbol, last_time, timestamp))

            self.last_update_time[symbol] = timestamp
            
        except Exception as e:
            self.logger.error(f"Error processing realtime data: {e}")

    async def save_to_db(self, symbol, timestamp, price, volume):
        """
        Save market data to SQLite.
        """
        query = """
            INSERT INTO market_data (timestamp, symbol, interval, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        # For tick data, we might aggregate or save as is. 
        # Assuming 1-minute aggregation or raw tick storage.
        # Here we save as '1m' candle update (simplified)
        # In real app, we would aggregate ticks into candles.
        # For now, let's just save the tick as a 'tick' interval or update current candle.
        # Let's assume we save raw tick for now or simplified candle.
        
        # Simplified: Save as 'tick'
        await db.execute(query, (timestamp, symbol, 'tick', price, price, price, price, volume))

    async def fill_gap(self, symbol, start_time, end_time):
        """
        Fetch missing data via REST API.
        """
        self.logger.info(f"Filling gap for {symbol} from {start_time} to {end_time}")
        try:
            # Call REST API to get OHLCV
            # In real implementation, we calculate how many candles are missing
            # and request them.
            # data = await self.rest_client.get_ohlcv(symbol, "1m", start_time, end_time)
            
            # Mocking the fetch
            self.logger.info(f"Gap filled for {symbol} (Mocked)")
            
        except Exception as e:
            self.logger.error(f"Gap filling failed: {e}")

    async def sync_symbol_master(self):
        """
        Sync Symbol Master (Code List) from API.
        """
        self.logger.info("Syncing Symbol Master...")
        # In real app: GetCodeListByMarket -> Save to DB
        # For now: Mock
        self.logger.info("Symbol Master Synced (Mocked)")

    async def subscribe_symbol(self, symbol):
        """
        Subscribe to a symbol.
        """
        await self.ws_client.subscribe("H0STCNT0", symbol)

    async def _schedule_monitor(self):
        """
        Monitor market schedule.
        """
        while True:
            is_open = self.market_schedule.check_market_status()
            # Notify status
            status_event = {
                "type": "STATUS",
                "market_open": is_open,
                "api_connected": self.ws_client.is_connected
            }
            await self.notify_observers(status_event)
            await asyncio.sleep(60)

    async def _macro_monitor(self):
        """
        Monitor macro data.
        """
        while True:
            await self.macro_collector.update_market_indices()
            await self.macro_collector.update_exchange_rate()
            
            macro_event = {
                "type": "MACRO",
                "indices": self.macro_collector.indices,
                "exchange_rate": self.macro_collector.exchange_rate
            }
            await self.notify_observers(macro_event)
            await asyncio.sleep(60)

    async def notify_observers(self, data):
        """
        Notify all observers.
        """
        for observer in self.observers:
            try:
                if asyncio.iscoroutinefunction(observer):
                    await observer(data)
                else:
                    observer(data)
            except Exception as e:
                self.logger.error(f"Observer notification failed: {e}")

data_collector = DataCollector()
