import asyncio
import os
from core.config import config
from core.logger import get_logger
from core.secure_storage import secure_storage
from core.database import db

logger = get_logger("CoreTest")

async def main():
    logger.info("Starting Core Module Test...")

    # 1. Config Test
    logger.info(f"Config DB_PATH: {config.get('DB_PATH')}")
    
    # 2. Secure Storage Test
    try:
        secure_storage.save("test_key", "secret_value")
        val = secure_storage.get("test_key")
        logger.info(f"Secure Storage Test: {'PASS' if val == 'secret_value' else 'FAIL'}")
        secure_storage.delete("test_key")
    except Exception as e:
        logger.error(f"Secure Storage Test Failed: {e}")

    # 3. Database Test
    try:
        await db.connect()
        # Insert dummy data
        await db.execute("INSERT OR IGNORE INTO market_data VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                         ('2023-01-01 09:00:00', '005930', '1m', 60000, 61000, 59000, 60500, 1000))
        
        rows = await db.fetch_all("SELECT * FROM market_data WHERE symbol='005930'")
        logger.info(f"Database Fetch Test: Found {len(rows)} rows")
        
        await db.close()
    except Exception as e:
        logger.error(f"Database Test Failed: {e}")

    logger.info("Core Module Test Completed.")

if __name__ == "__main__":
    asyncio.run(main())
