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
        self.ws_client.add_callback(self.macro_collector.on_realtime_data)
        
        # Subscribe to internal events
        from core.event_bus import event_bus
        event_bus.subscribe("watchlist.updated", self._on_watchlist_updated)

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
        # Start background tasks
        asyncio.create_task(self._schedule_monitor())
        asyncio.create_task(self.macro_collector.start_scheduler())
        
        # Load Conditions (No Auto-Subscribe)
        asyncio.create_task(self.load_conditions())

    async def load_conditions(self):
        """
        Load conditions from API.
        """
        try:
            conditions = await self.rest_client.get_condition_load()
            if conditions and "output" in conditions:
                self.condition_list = conditions["output"]
                self.logger.info(f"Loaded {len(self.condition_list)} conditions.")
        except Exception as e:
            self.logger.error(f"Failed to load conditions: {e}")

    async def subscribe_condition(self, index, name):
        """
        Subscribe to a specific condition.
        """
        self.logger.info(f"Subscribing to Condition: {name} ({index})")
        # Use a fixed screen number range for conditions or "1000"
        await self.rest_client.send_condition("1000", name, index, "0")

    async def unsubscribe_condition(self, index, name):
        """
        Unsubscribe from a specific condition.
        """
        self.logger.info(f"Unsubscribing from Condition: {name} ({index})")
        await self.rest_client.stop_condition("1000", name, index)

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

    async def get_recent_data(self, symbol: str, limit: int = 100) -> pd.DataFrame:
        """
        Get recent market data for strategy analysis.
        Combines DB history and realtime buffer.
        """
        try:
            # 1. Fetch from DB
            query = f"""
                SELECT timestamp, open, high, low, close, volume 
                FROM market_data 
                WHERE symbol = ? AND interval = '1m' 
                ORDER BY timestamp DESC LIMIT ?
            """
            async with db.execute(query, (symbol, limit)) as cursor:
                rows = await cursor.fetchall()
                
            if not rows:
                return pd.DataFrame()
                
            # Convert to DataFrame
            df = pd.DataFrame(rows, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
            
            return df
        except Exception as e:
            self.logger.error(f"Failed to get recent data: {e}")
            return pd.DataFrame()

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
        Handles both Market Data and Condition Events.
        """
        try:
            # 1. Condition Event Handling
            if "condition_index" in data:
                await self._on_condition_event(data)
                return

            # 2. Market Data Handling
            # Check Market Hours
            if not self.market_schedule.check_market_status():
                return

            symbol = data.get("code")
            price = float(data.get("price", 0))
            volume = int(data.get("volume", 0))
            timestamp = datetime.now() 
            
            if not symbol:
                return

            # Update Buffer & Save to DB
            # self.logger.debug(f"Realtime Data: {symbol} - {price}")
            
            # Save Tick
            await self.save_to_db(symbol, timestamp, price, volume, interval='tick')
            
            # Aggregate Candle (1-minute)
            await self._aggregate_candle(symbol, timestamp, price, volume)
            
            # Notify Observers (UI)
            data['type'] = 'REALTIME'
            await self.notify_observers(data)
            
            # Gap Filling Check
            last_time = self.last_update_time.get(symbol)
            if last_time:
                time_diff = (timestamp - last_time).total_seconds()
                if time_diff > 60: 
                    self.logger.warning(f"Gap detected for {symbol} ({time_diff}s). Triggering Gap Filling...")
                    asyncio.create_task(self.fill_gap(symbol, last_time, timestamp))

            self.last_update_time[symbol] = timestamp
            
        except Exception as e:
            self.logger.error(f"Error processing realtime data: {e}")

    async def _on_condition_event(self, data):
        """
        Handle Condition Search Events (Insert/Delete).
        """
        try:
            # data structure: {condition_index, condition_name, code, type (I/D)}
            c_index = data.get("condition_index")
            c_name = data.get("condition_name")
            code = data.get("code")
            event_type = data.get("type") # 'I' (Insert) or 'D' (Delete)
            
            self.logger.info(f"Condition Event: [{event_type}] {code} @ {c_name}")
            
            # Publish to EventBus
            from core.event_bus import event_bus
            event_bus.publish("CONDITION_MATCH", {
                "symbol": code,
                "condition_index": c_index,
                "condition_name": c_name,
                "type": event_type, # 'INSERT' or 'DELETE'
                "timestamp": datetime.now()
            })
            
            # Also notify observers directly if needed (e.g. UI log)
            await self.notify_observers({
                "type": "CONDITION",
                "symbol": code,
                "condition_name": c_name,
                "event": "INSERT" if event_type == 'I' else "DELETE"
            })
            
        except Exception as e:
            self.logger.error(f"Error handling condition event: {e}")

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
        Fetch missing data via REST API and Bulk Insert.
        """
        self.logger.info(f"Filling gap for {symbol} from {start_time} to {end_time}")
        try:
            # Convert start_time to YYYYMMDD
            start_date = start_time.strftime("%Y%m%d")
            
            # Fetch Minute Data
            ohlcv_data = await self.rest_client.get_ohlcv(symbol, "minute", start_date)
            
            if ohlcv_data and "output" in ohlcv_data:
                bulk_data = []
                for candle in ohlcv_data["output"]:
                    # Robust Timestamp Parsing
                    date_str = candle.get("date", "").strip()
                    time_str = candle.get("time", "").strip() # Some TRs return time separately
                    
                    ts = None
                    try:
                        if len(date_str) == 14: # YYYYMMDDHHMMSS
                            ts = datetime.strptime(date_str, "%Y%m%d%H%M%S")
                        elif len(date_str) == 8: # YYYYMMDD
                            if len(time_str) == 6: # HHMMSS
                                ts = datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S")
                            elif len(time_str) == 4: # HHMM
                                ts = datetime.strptime(f"{date_str}{time_str}00", "%Y%m%d%H%M%S")
                            else:
                                # Fallback: if minute data but no time, might be daily or error. 
                                # For minute gap filling, we need time. 
                                # If missing, maybe skip or use end of day?
                                # Let's assume 00:00:00 if missing, but that's risky for minute data.
                                # Check if 'date' actually contains time in some other format?
                                ts = datetime.strptime(date_str, "%Y%m%d") 
                        else:
                            continue # Skip invalid format
                    except ValueError:
                        continue

                    if ts:
                        # Prepare tuple for bulk insert
                        # (timestamp, symbol, interval, open, high, low, close, volume)
                        c = int(candle.get("close", 0))
                        o = int(candle.get("open", c))
                        h = int(candle.get("high", c))
                        l = int(candle.get("low", c))
                        v = int(candle.get("volume", 0))
                        
                        bulk_data.append((ts, symbol, '1m', o, h, l, c, v))

                if bulk_data:
                    query = """
                        INSERT OR REPLACE INTO market_data (timestamp, symbol, interval, open, high, low, close, volume)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    count = await db.execute_many(query, bulk_data)
                    self.logger.info(f"Gap filled for {symbol}: {count} candles inserted.")
                else:
                    self.logger.warning(f"No valid candles parsed for {symbol}")
            else:
                self.logger.warning(f"No data found for gap filling: {symbol}")
            
        except Exception as e:
            self.logger.error(f"Gap filling failed: {e}")

    async def sync_symbol_master(self):
        """
        Sync Symbol Master (Code List) from API using Bulk Insert.
        """
        self.logger.info("Syncing Symbol Master...")
        try:
            # KOSPI (0) & KOSDAQ (10)
            markets = {"0": "KOSPI", "10": "KOSDAQ"}
            
            for market_type, market_name in markets.items():
                codes = await self.rest_client.get_code_list(market_type)
                if codes:
                    self.logger.info(f"Fetched {len(codes)} codes for {market_name}")
                    
                    # Prepare bulk data
                    # (code, name, market, updated_at) - updated_at is handled by DB default usually, 
                    # but for executemany we might need to supply it or let DB handle it if we omit it?
                    # Our query in loop was: VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    # We can use the same query structure.
                    
                    bulk_data = [(code, "", market_name) for code in codes]
                    
                    query = """
                        INSERT OR REPLACE INTO market_code (code, name, market, updated_at)
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    """
                    
                    await db.execute_many(query, bulk_data)
                        
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



    async def _on_watchlist_updated(self, event):
        """
        Handle watchlist update event.
        event.data: {'codes': ['005930', ...]}
        """
        try:
            data = event.data
            codes = data.get("codes", [])
            if not codes:
                return
                
            self.logger.info(f"Updating Watchlist Subscription: {len(codes)} symbols")
            
            # Batch Subscribe
            # Kiwoom WS supports multiple codes separated by ';' (Max length check needed?)
            # Let's chunk them just in case (e.g., 50 at a time)
            chunk_size = 50
            for i in range(0, len(codes), chunk_size):
                chunk = codes[i:i+chunk_size]
                joined_codes = ";".join(chunk)
                await self.ws_client.subscribe("H0STCNT0", joined_codes)
                await asyncio.sleep(0.1) # Small delay between chunks
                
        except Exception as e:
            self.logger.error(f"Failed to update watchlist subscription: {e}")

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
