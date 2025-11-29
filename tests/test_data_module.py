import unittest
import asyncio
import time
from unittest.mock import MagicMock, patch, AsyncMock
from data.rate_limiter import RateLimiter
from data.kiwoom_rest_client import KiwoomRestClient

class TestRateLimiter(unittest.TestCase):
    def test_rate_limiter(self):
        async def run_test():
            # Allow 5 tokens, refill 5 per second (1 token every 0.2s)
            limiter = RateLimiter(max_tokens=5, refill_rate=5)
            
            # Consume 5 tokens instantly
            start = time.monotonic()
            for _ in range(5):
                await limiter.acquire()
            duration = time.monotonic() - start
            self.assertLess(duration, 0.1, "First 5 tokens should be instant")

            # Consume 1 more token (should wait ~0.2s)
            start = time.monotonic()
            await limiter.acquire()
            duration = time.monotonic() - start
            self.assertGreater(duration, 0.15, "Should wait for refill")
            print(f"RateLimiter Test: Waited {duration:.4f}s for refill")

        asyncio.run(run_test())

class TestKiwoomRestClient(unittest.TestCase):
    @patch('data.kiwoom_rest_client.aiohttp.ClientSession')
    def test_get_token(self, mock_session_cls):
        async def run_test():
            client = KiwoomRestClient()
            
            # Mock Response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "access_token": "test_token_123",
                "expires_in": 3600
            }
            
            # Mock Session Context Manager
            # session.post() returns a context manager, NOT a coroutine.
            # So mock_session.post should be a MagicMock (default for child of AsyncMock is AsyncMock, so we force it)
            mock_session = MagicMock() 
            
            # The context manager returned by post()
            post_ctx = AsyncMock()
            post_ctx.__aenter__.return_value = mock_response
            
            mock_session.post.return_value = post_ctx
            
            # Configure close() to be awaitable
            mock_session.close = AsyncMock()

            # Configure ClientSession() to return our mock session
            # ClientSession() itself is usually awaited or used as context manager, 
            # but here we use it as `await self._get_session()` which returns the session object.
            # In the code: session = await self._get_session() -> returns self.session
            # self.session = aiohttp.ClientSession() -> This is not awaited in __init__, but _get_session creates it.
            # Wait, _get_session is async but aiohttp.ClientSession() is synchronous constructor.
            # The code: self.session = aiohttp.ClientSession()
            
            # In the test, we patch 'data.kiwoom_rest_client.aiohttp.ClientSession'.
            # The code calls `self.session = aiohttp.ClientSession()`.
            # So mock_session_cls() returns the session object.
            mock_session_cls.return_value = mock_session
            
            # Test Token Issuance
            token = await client.get_token()
            self.assertEqual(token, "test_token_123")
            self.assertIsNotNone(client.token_expiry)
            print("KiwoomRestClient Token Test: PASS")

            # Test Token Reuse (Should not call API again)
            mock_session.post.reset_mock()
            token2 = await client.get_token()
            self.assertEqual(token2, "test_token_123")
            mock_session.post.assert_not_called()
            print("KiwoomRestClient Token Reuse Test: PASS")
            
            await client.close()

        asyncio.run(run_test())

from data.websocket_client import WebSocketClient

class TestWebSocketClient(unittest.TestCase):
    @patch('data.websocket_client.websockets.connect', new_callable=AsyncMock)
    def test_websocket_flow(self, mock_connect):
        async def run_test():
            client = WebSocketClient()
            
            # Mock WebSocket Connection
            mock_ws = AsyncMock()
            mock_connect.return_value = mock_ws
            
            # 1. Test Connect
            await client.connect()
            self.assertTrue(client.is_connected)
            mock_connect.assert_called_once()
            print("WebSocket Connect Test: PASS")

            # 2. Test Subscribe
            await client.subscribe("H0STCNT0", "005930")
            mock_ws.send.assert_called_once()
            sent_json = mock_ws.send.call_args[0][0]
            self.assertIn("005930", sent_json)
            print("WebSocket Subscribe Test: PASS")

            # 3. Test Message Handling
            # Setup callback
            received_data = []
            async def on_data(data):
                received_data.append(data)
            
            client.add_callback(on_data)

            # Simulate incoming message
            # We need to simulate the loop in _listen. 
            # Since _listen is running in background task, we can't easily mock recv() sequence for it 
            # unless we wait or inject.
            # Instead, let's test _handle_message directly for unit testing logic.
            
            test_msg = '{"code": "005930", "price": 70000}'
            await client._handle_message(test_msg)
            
            self.assertEqual(len(received_data), 1)
            self.assertEqual(received_data[0]['price'], 70000)
            print("WebSocket Message Handling Test: PASS")

            # 4. Test Disconnect
            await client.disconnect()
            self.assertFalse(client.is_connected)
            mock_ws.close.assert_called_once()
            print("WebSocket Disconnect Test: PASS")

        asyncio.run(run_test())

from data.market_schedule import MarketSchedule
from datetime import time as dt_time

class TestMarketSchedule(unittest.TestCase):
    def test_market_schedule(self):
        schedule = MarketSchedule()
        
        # Mock datetime to simulate market open
        with patch('data.market_schedule.datetime') as mock_datetime:
            mock_datetime.now.return_value.time.return_value = dt_time(10, 0) # 10:00 AM
            self.assertTrue(schedule.check_market_status())
            
            # Mock datetime to simulate market close
            mock_datetime.now.return_value.time.return_value = dt_time(16, 0) # 4:00 PM
            self.assertFalse(schedule.check_market_status())
            
        print("MarketSchedule Status Test: PASS")

from data.data_collector import DataCollector
from datetime import datetime, timedelta

class TestDataCollector(unittest.TestCase):
    @patch('data.data_collector.kiwoom_client')
    @patch('data.data_collector.ws_client')
    @patch('data.data_collector.db')
    @patch('data.data_collector.market_schedule')
    def test_data_collector_flow(self, mock_schedule, mock_db, mock_ws_client, mock_rest_client):
        async def run_test():
            collector = DataCollector()
            # Inject mocks
            collector.ws_client = mock_ws_client
            collector.rest_client = mock_rest_client
            collector.market_schedule = mock_schedule
            
            # 1. Test Start (DB Connect & Symbol Sync)
            mock_ws_client.connect = AsyncMock()
            mock_db.connect = AsyncMock()
            collector.sync_symbol_master = AsyncMock() # Mock internal method
            
            await collector.start()
            
            mock_db.connect.assert_called_once()
            collector.sync_symbol_master.assert_called_once()
            mock_ws_client.connect.assert_called_once()
            print("DataCollector Start Test: PASS")

            # 2. Test Subscribe
            mock_ws_client.subscribe = AsyncMock()
            await collector.subscribe_symbol("005930")
            mock_ws_client.subscribe.assert_called_with("H0STCNT0", "005930")
            print("DataCollector Subscribe Test: PASS")

            # 3. Test Realtime Data & DB Save
            # Case A: Market Open
            mock_schedule.check_market_status.return_value = True
            mock_db.execute = AsyncMock()
            
            data_normal = {"code": "005930", "price": 70000, "volume": 100}
            await collector.on_realtime_data(data_normal)
            
            self.assertIn("005930", collector.last_update_time)
            mock_db.execute.assert_called_once() # Should save to DB
            print("DataCollector Realtime Update & DB Save Test: PASS")

            # Case B: Market Closed (Should ignore data)
            mock_schedule.check_market_status.return_value = False
            mock_db.execute.reset_mock()
            
            await collector.on_realtime_data(data_normal)
            mock_db.execute.assert_not_called()
            print("DataCollector Market Closed Test: PASS")

            # Case C: Gap Detection
            mock_schedule.check_market_status.return_value = True
            # Manually set last update time to 70 seconds ago
            collector.last_update_time["005930"] = datetime.now() - timedelta(seconds=70)
            
            # Mock fill_gap to verify it's called
            collector.fill_gap = AsyncMock()
            
            await collector.on_realtime_data(data_normal)
            
            collector.fill_gap.assert_called_once()
            print("DataCollector Gap Filling Trigger Test: PASS")

            # 4. Test Stop
            mock_ws_client.disconnect = AsyncMock()
            mock_rest_client.close = AsyncMock()
            mock_db.close = AsyncMock()
            
            await collector.stop()
            
            mock_ws_client.disconnect.assert_called_once()
            mock_rest_client.close.assert_called_once()
            mock_db.close.assert_called_once()
            print("DataCollector Stop Test: PASS")

        asyncio.run(run_test())

from data.macro_collector import MacroCollector
from data.indicator_engine import IndicatorEngine
import pandas as pd
import numpy as np

class TestMacroCollector(unittest.TestCase):
    @patch('data.macro_collector.kiwoom_client')
    def test_macro_collector(self, mock_rest_client):
        async def run_test():
            collector = MacroCollector()
            collector.rest_client = mock_rest_client
            
            # Mock Kiwoom API response for Indices
            # MacroCollector calls get_market_index, so we must mock that method on the client
            mock_rest_client.get_market_index = AsyncMock(side_effect=[
                {"output": {"price": "2,600.00"}}, # KOSPI (String with comma)
                {"output": {"price": "900.00"}}    # KOSDAQ
            ])
            
            await collector.update_market_indices()
            self.assertEqual(collector.indices["KOSPI"], 2600.0)
            self.assertEqual(collector.indices["KOSDAQ"], 900.0)
            print("MacroCollector Indices Test: PASS")

            # Mock External API for Exchange Rate
            with patch('data.macro_collector.aiohttp.ClientSession') as mock_session_cls:
                mock_session = MagicMock()
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = {"rates": {"KRW": 1350.0}}
                
                # Context manager setup for session.get()
                get_ctx = AsyncMock()
                get_ctx.__aenter__.return_value = mock_response
                mock_session.get.return_value = get_ctx
                
                mock_session_cls.return_value.__aenter__.return_value = mock_session
                
                await collector.update_exchange_rate()
                self.assertEqual(collector.exchange_rate, 1350.0)
                print("MacroCollector Exchange Rate Test: PASS")

        asyncio.run(run_test())

class TestIndicatorEngine(unittest.TestCase):
    def test_indicator_calculation(self):
        engine = IndicatorEngine()
        
        # Create dummy DataFrame
        data = {
            'close': np.random.random(100) * 100,
            'high': np.random.random(100) * 100,
            'low': np.random.random(100) * 100,
            'volume': np.random.random(100) * 1000
        }
        df = pd.DataFrame(data)
        
        # Calculate Indicators
        df_result = engine.add_indicators(df)
        
        # Verify Columns
        expected_columns = ['MA5', 'MA20', 'RSI14', 'BB_UPPER', 'MACD', 'ATR14']
        for col in expected_columns:
            self.assertIn(col, df_result.columns)
        
        # Verify Values (Check last row is not NaN for short period indicators)
        self.assertFalse(pd.isna(df_result['MA5'].iloc[-1]))
        self.assertFalse(pd.isna(df_result['RSI14'].iloc[-1]))
        
        print("IndicatorEngine Calculation Test: PASS")

if __name__ == '__main__':
    unittest.main()
