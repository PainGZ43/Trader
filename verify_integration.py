import asyncio
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Force Mock Mode for Verification
os.environ["MOCK_MODE"] = "True"
os.environ["LOG_LEVEL"] = "DEBUG"

from core.config import ConfigLoader
from core.logger import get_logger
from core.database import db
from data.data_collector import DataCollector

async def verify_integration():
    logger = get_logger("IntegrationVerifier")
    logger.info("Starting Integration Verification (MOCK_MODE=True)...")
    
    # 1. Initialize Components
    collector = DataCollector()
    
    # Patch MarketSchedule to force Open
    with patch.object(collector.market_schedule, 'check_market_status', return_value=True):
        
        # 2. Start Collector
        await collector.start()
        
        # 3. Verify Market Code Sync
        logger.info("Verifying Market Code Sync...")
        rows = await db.fetch_all("SELECT count(*) FROM market_code")
        code_count = rows[0][0]
        if code_count > 0:
            logger.info(f"SUCCESS: Found {code_count} market codes.")
        else:
            logger.error("FAILURE: No market codes found.")
            sys.exit(1)

        # 4. Subscribe & Simulate Data for Candle
        test_symbol = "005930"
        await collector.subscribe_symbol(test_symbol)
        logger.info(f"Subscribed to {test_symbol}. Simulating data flow...")
        
        # Inject data manually to test aggregation logic without waiting 60s
        base_time = datetime(2024, 1, 1, 10, 0, 0)
        
        # Tick 1: 10:00:10
        with patch('data.data_collector.datetime') as mock_dt:
            mock_dt.now.return_value = base_time + timedelta(seconds=10)
            await collector.on_realtime_data({"code": test_symbol, "price": 1000, "volume": 10})
            
        # Tick 2: 10:00:50
        with patch('data.data_collector.datetime') as mock_dt:
            mock_dt.now.return_value = base_time + timedelta(seconds=50)
            await collector.on_realtime_data({"code": test_symbol, "price": 1010, "volume": 20})
            
        # Tick 3: 10:01:05 (Triggers Candle Close for 10:00)
        with patch('data.data_collector.datetime') as mock_dt:
            mock_dt.now.return_value = base_time + timedelta(minutes=1, seconds=5)
            await collector.on_realtime_data({"code": test_symbol, "price": 1005, "volume": 5})
            
        # 5. Verify Database Content
        logger.info("Verifying Database Content...")
        
        # Check Ticks
        tick_rows = await db.fetch_all(f"SELECT count(*) FROM market_data WHERE symbol='{test_symbol}' AND interval='tick'")
        tick_count = tick_rows[0][0]
        logger.info(f"Tick Count: {tick_count}")
        
        # Check 1m Candle
        candle_rows = await db.fetch_all(f"SELECT count(*) FROM market_data WHERE symbol='{test_symbol}' AND interval='1m'")
        candle_count = candle_rows[0][0]
        logger.info(f"Candle Count: {candle_count}")
        
        # 6. Stop
        await collector.stop()
        
        if tick_count >= 3 and candle_count >= 1:
            print("\n[VERIFICATION RESULT] PASS: Core <-> Data Module Integration Successful.")
            print(f"- Market Codes: {code_count}")
            print(f"- Ticks Saved: {tick_count}")
            print(f"- Candles Generated: {candle_count}")
            sys.exit(0)
        else:
            print("\n[VERIFICATION RESULT] FAIL: Data missing.")
            sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(verify_integration())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Verification Failed with Error: {e}")
        sys.exit(1)
