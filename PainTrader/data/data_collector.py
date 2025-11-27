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
        
        # Cleanup Old Data
        await db.cleanup_old_data()
        
        await self.sync_symbol_master()
        await self.ws_client.connect()
        
        # Start background tasks
        asyncio.create_task(self._schedule_monitor())
        asyncio.create_task(self._macro_monitor())
        
        # Load & Subscribe Conditions
        asyncio.create_task(self.load_and_subscribe_conditions())

    async def load_and_subscribe_conditions(self):
        """
        Load conditions and subscribe to them.
        """
        try:
            conditions = await self.rest_client.get_condition_load()
            if conditions and "output" in conditions:
                for cond in conditions["output"]:
                    idx = cond["index"]
                    name = cond["name"]
                    self.logger.info(f"Subscribing to Condition: {name} ({idx})")
                    # Real-time search (type "0")
                    # Screen number can be arbitrary unique per condition or shared
                    await self.rest_client.send_condition("1000", name, idx, "0")
        except Exception as e:
            self.logger.error(f"Failed to load conditions: {e}")

    async def get_condition_list(self):
        """
        Get list of available conditions.
        Returns: List of dicts [{'index': '001', 'name': 'Golden Cross'}, ...]
        """
        try:
            conditions = await self.rest_client.get_condition_load()
            if conditions and "output" in conditions:
                return conditions["output"]
            return []
        except Exception as e:
            self.logger.error(f"Failed to get condition list: {e}")
            return []

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
            price = float(data.get("price"))
            volume = int(data.get("volume", 0))
            timestamp = datetime.now() # Or use server timestamp if available
            
            if not symbol:
                return

            # Update Buffer & Save to DB
            self.logger.debug(f"Realtime Data: {symbol} - {price}")
            
            # 1. Save Tick (Optional: based on retention policy, maybe skip or save to separate table)
            # For now, we save tick as 'tick' interval
            await self.save_to_db(symbol, timestamp, price, volume, interval='tick')
            
            # 2. Aggregate Candle (1-minute)
            await self._aggregate_candle(symbol, timestamp, price, volume)
            
            # Notify Observers (UI)
            data['type'] = 'REALTIME'
            await self.notify_observers(data)
            
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

    async def _aggregate_candle(self, symbol, timestamp, price, volume):
        """
        Aggregate ticks into 1-minute candles.
        """
        # Initialize buffer if needed
        if symbol not in self.realtime_buffer:
            self.realtime_buffer[symbol] = {
                "open": price, "high": price, "low": price, "close": price, "volume": 0,
                "start_time": timestamp.replace(second=0, microsecond=0)
            }
        
        candle = self.realtime_buffer[symbol]
        
        # Check if minute changed
        current_minute = timestamp.replace(second=0, microsecond=0)
        if current_minute > candle["start_time"]:
            # Candle Closed -> Save & Publish
            await self.save_to_db(
                symbol, candle["start_time"], 
                candle["close"], candle["volume"], 
                interval='1m',
                open_p=candle["open"], high_p=candle["high"], low_p=candle["low"]
            )
            
            # Publish Event (CANDLE_CLOSED)
            from core.event_bus import event_bus
            event_bus.publish("CANDLE_CLOSED", {
                "symbol": symbol,
                "interval": "1m",
                "timestamp": candle["start_time"],
                "open": candle["open"],
                "high": candle["high"],
                "low": candle["low"],
                "close": candle["close"],
                "volume": candle["volume"]
            })
            
            # Reset Buffer for new minute
            self.realtime_buffer[symbol] = {
                "open": price, "high": price, "low": price, "close": price, "volume": volume,
                "start_time": current_minute
            }
        else:
            # Update current candle
            candle["high"] = max(candle["high"], price)
            candle["low"] = min(candle["low"], price)
            candle["close"] = price
            candle["volume"] += volume

    async def save_to_db(self, symbol, timestamp, close, volume, interval='tick', open_p=None, high_p=None, low_p=None):
        """
        Save market data to SQLite.
        """
        query = """
            INSERT OR REPLACE INTO market_data (timestamp, symbol, interval, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        if open_p is None: open_p = close
        if high_p is None: high_p = close
        if low_p is None: low_p = close
        
        await db.execute(query, (timestamp, symbol, interval, open_p, high_p, low_p, close, volume))

    async def fill_gap(self, symbol, start_time, end_time):
        """
        Fetch missing data via REST API.
        """
        self.logger.info(f"Filling gap for {symbol} from {start_time} to {end_time}")
        try:
            # Convert start_time to YYYYMMDD
            start_date = start_time.strftime("%Y%m%d")
            
            # Fetch Minute Data (assuming 1m gap)
            ohlcv_data = await self.rest_client.get_ohlcv(symbol, "minute", start_date)
            
            if ohlcv_data and "output" in ohlcv_data:
                for candle in ohlcv_data["output"]:
                    # Parse candle time (YYYYMMDDHHMMSS)
                    # Note: Kiwoom returns time in a specific format, need to parse carefully.
                    # For minute data, it usually returns 'date' (YYYYMMDD) and 'time' (HHMMSS) or combined.
                    # Let's assume standard format for now or just use the date provided.
                    # In real Kiwoom, minute data has 'che_time' or similar.
                    # For this implementation, we assume 'date' is YYYYMMDD and we might need time.
                    # If mock data, we trust it.
                    
                    # Simplified: Just save what we got
                    # In production, we need precise timestamp parsing.
                    ts_str = candle.get("date") # YYYYMMDD or YYYYMMDDHHMMSS
                    try:
                        if len(ts_str) == 8:
                            ts = datetime.strptime(ts_str, "%Y%m%d")
                        elif len(ts_str) == 14:
                            ts = datetime.strptime(ts_str, "%Y%m%d%H%M%S")
                        else:
                            ts = datetime.now() # Fallback
                    except:
                        ts = datetime.now()

                    await self.save_to_db(
                        symbol, 
                        ts, 
                        int(candle.get("close")), 
                        int(candle.get("volume"))
                    )
                self.logger.info(f"Gap filled for {symbol} ({len(ohlcv_data['output'])} candles)")
            else:
                self.logger.warning(f"No data found for gap filling: {symbol}")
            
        except Exception as e:
            self.logger.error(f"Gap filling failed: {e}")

    async def sync_symbol_master(self):
        """
        Sync Symbol Master (Code List) from API.
        """
        self.logger.info("Syncing Symbol Master...")
        try:
            # KOSPI (0) & KOSDAQ (10)
            markets = {"0": "KOSPI", "10": "KOSDAQ"}
            
            for market_type, market_name in markets.items():
                codes = await self.rest_client.get_code_list(market_type)
                if codes:
                    self.logger.info(f"Fetched {len(codes)} codes for {market_name}")
                    for code in codes:
                        # Get Name (Optional: need another API call or get_master_code_name equivalent)
                        # For now, we just save code and market. Name can be updated later or if API provides it.
                        # Kiwoom REST might not provide name in code_list directly.
                        # We will insert code and market.
                        
                        query = """
                            INSERT OR REPLACE INTO market_code (code, name, market, updated_at)
                            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                        """
                        # Name is empty for now
                        await db.execute(query, (code, "", market_name))
                        
            self.logger.info("Symbol Master Synced")
        except Exception as e:
            self.logger.error(f"Symbol Master Sync Failed: {e}")

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
