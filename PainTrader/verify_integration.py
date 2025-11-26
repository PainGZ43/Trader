import asyncio
import os
import sys
from datetime import datetime

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
    
    # 2. Start Collector (Connects to Mock WS, Syncs Master, Starts Monitors)
    await collector.start()
    
    # 3. Subscribe to a symbol
    test_symbol = "005930" # Samsung Electronics
    await collector.subscribe_symbol(test_symbol)
    
    logger.info(f"Subscribed to {test_symbol}. Waiting for data (5 seconds)...")
    await asyncio.sleep(5)
    
    # 4. Verify Database
    logger.info("Verifying Database Content...")
    rows = await db.fetch_all(f"SELECT count(*) FROM market_data WHERE symbol = '{test_symbol}'")
    count = rows[0][0]
        
    if count > 0:
        logger.info(f"SUCCESS: Found {count} records for {test_symbol} in database.")
    else:
        logger.error(f"FAILURE: No records found for {test_symbol} in database.")
        
    # 5. Verify Gap Filling (Simulate by manually checking log or just trust unit test)
    # For integration, basic data flow is key.
    
    # 6. Stop
    await collector.stop()
    
    if count > 0:
        print("\n[VERIFICATION RESULT] PASS: Data flow from WebSocket to DB is working.")
        sys.exit(0)
    else:
        print("\n[VERIFICATION RESULT] FAIL: No data saved to DB.")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(verify_integration())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Verification Failed with Error: {e}")
        sys.exit(1)
