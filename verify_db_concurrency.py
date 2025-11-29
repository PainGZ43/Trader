import asyncio
import sys
import os
import random
import time
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import db
from core.logger import get_logger

logger = get_logger("DB_TEST")

async def writer_task(task_id, iterations):
    """
    Simulates a data collector writing market data.
    """
    logger.info(f"Writer {task_id} started.")
    try:
        for i in range(iterations):
            symbol = f"TEST_{task_id}"
            price = 1000 + i
            timestamp = datetime.now()
            
            query = """
                INSERT OR REPLACE INTO market_data (timestamp, symbol, interval, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            await db.execute(query, (timestamp, symbol, '1m', price, price, price, price, 100))
            
            if i % 100 == 0:
                print(f"Writer {task_id}: {i}/{iterations}")
            
            # Random small sleep to simulate real-time data arrival
            await asyncio.sleep(random.uniform(0.001, 0.01))
            
    except Exception as e:
        logger.error(f"Writer {task_id} failed: {e}")
        return False
    
    logger.info(f"Writer {task_id} finished.")
    return True

async def reader_task(task_id, iterations):
    """
    Simulates a UI component reading data.
    """
    logger.info(f"Reader {task_id} started.")
    try:
        for i in range(iterations):
            query = "SELECT count(*) as cnt FROM market_data"
            result = await db.fetch_all(query)
            count = result[0]['cnt']
            
            if i % 100 == 0:
                print(f"Reader {task_id}: Count={count}")
                
            await asyncio.sleep(random.uniform(0.005, 0.02))
            
    except Exception as e:
        logger.error(f"Reader {task_id} failed: {e}")
        return False
        
    logger.info(f"Reader {task_id} finished.")
    return True

async def run_stress_test():
    print("=== Starting Database Concurrency Stress Test ===")
    
    # Initialize DB (Connect & Create Tables)
    max_retries = 5
    for attempt in range(max_retries):
        try:
            await db.connect()
            break
        except Exception as e:
            print(f"Connection attempt {attempt+1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(1)
            else:
                print("Failed to connect to DB after retries. Is another instance running?")
                return
    
    # Check WAL mode
    wal_check = await db.fetch_all("PRAGMA journal_mode;")
    print(f"Journal Mode: {wal_check[0][0]}")
    
    if wal_check[0][0].upper() != 'WAL':
        print("WARNING: WAL mode is NOT enabled!")
    else:
        print("SUCCESS: WAL mode is enabled.")

    # Configuration
    num_writers = 2
    num_readers = 5
    iterations = 100
    
    tasks = []
    
    start_time = time.time()
    
    # Spawn Writers
    for i in range(num_writers):
        tasks.append(asyncio.create_task(writer_task(i, iterations)))
        
    # Spawn Readers
    for i in range(num_readers):
        tasks.append(asyncio.create_task(reader_task(i, iterations)))
        
    # Wait for all
    results = await asyncio.gather(*tasks)
    
    end_time = time.time()
    duration = end_time - start_time
    
    success_count = sum(1 for r in results if r)
    fail_count = len(results) - success_count
    
    print("\n=== Test Results ===")
    print(f"Total Tasks: {len(results)}")
    print(f"Success: {success_count}")
    print(f"Failed: {fail_count}")
    print(f"Duration: {duration:.2f}s")
    
    if fail_count == 0:
        print("✅ CONCURRENCY TEST PASSED")
    else:
        print("❌ CONCURRENCY TEST FAILED")
        
    await db.close()

if __name__ == "__main__":
    try:
        asyncio.run(run_stress_test())
    except KeyboardInterrupt:
        print("Test interrupted.")
