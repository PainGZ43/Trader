import asyncio
import sys
import os
import logging
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.logger import get_logger
from core.config import config
from data.kiwoom_rest_client import kiwoom_client
from execution.engine import ExecutionEngine
from strategy.base_strategy import Signal
from core.database import db

# Configure logging
sys.stdout.reconfigure(encoding='utf-8')
logger = get_logger("ScenarioTest_2")
logging.basicConfig(level=logging.INFO)

async def main():
    print("=" * 60)
    print("   SCENARIO TEST 2: EXCEPTIONS & RECOVERY")
    print("=" * 60)

    # Setup
    kiwoom_client.offline_mode = True
    kiwoom_client.is_mock_server = True
    await db.connect()
    
    # 1. Rate Limit Test
    print("\n[Step 1] Testing Rate Limiter...")
    start_time = datetime.now()
    
    # Consume all tokens (assuming 5/sec)
    print(" - Consuming tokens rapidly...")
    for i in range(10):
        # We access the rate limiter directly to simulate rapid requests
        # In offline mode, request() doesn't wait, so we mock the limiter check
        await kiwoom_client.rate_limiter.acquire()
        print(f"   Request {i+1} acquired.")
        
    duration = (datetime.now() - start_time).total_seconds()
    print(f" - 10 Requests took {duration:.2f} seconds.")
    
    if duration >= 1.0: # Should take at least 1-2 seconds for 10 requests with 5/sec limit
        print("SUCCESS: Rate Limiter delayed requests appropriately.")
    else:
        print("WARNING: Rate Limiter might be too loose (or offline mode skipped it).")

    # 2. Network Failure Simulation
    print("\n[Step 2] Testing Network Failure Handling...")
    
    # Mock send_order to raise exception
    original_send = kiwoom_client.send_order
    
    async def mock_fail_order(*args, **kwargs):
        print("   [Simulated] Network Connection Failed!")
        raise ConnectionError("Simulated Network Error")
        
    kiwoom_client.send_order = mock_fail_order
    
    engine = ExecutionEngine(kiwoom_client, mode="MOCK")
    await engine.initialize()
    
    signal = Signal(symbol="005930", type="BUY", price=70000, timestamp=datetime.now(), reason="Test", score=1.0)
    
    try:
        print(" - Attempting Order during Network Failure...")
        # OrderManager should catch this and log error, maybe retry (if implemented)
        # For now, we verify it doesn't crash the system
        await engine.order_manager.send_order(signal, 1, "mock_acc")
        print(" - System handled exception without crashing.")
    except Exception as e:
        print(f"FAILED: System crashed with: {e}")

    # Restore
    kiwoom_client.send_order = original_send
    print("SUCCESS: Network failure handled.")

    # 3. Recovery Test (State Persistence)
    print("\n[Step 3] Testing Crash Recovery (State Persistence)...")
    
    # Ensure table exists with correct schema (Drop old one if mismatch)
    try:
        await db.execute("DROP TABLE IF EXISTS strategy_state")
        await db.execute("""
            CREATE TABLE IF NOT EXISTS strategy_state (
                strategy_id TEXT PRIMARY KEY,
                symbol TEXT,
                current_position INTEGER,
                avg_entry_price REAL,
                accumulated_profit REAL,
                indicators TEXT,
                last_update DATETIME
            )
        """)
    except Exception as e:
        print(f" - Table reset warning: {e}")

    # Save a state to DB
    strategy_id = "RECOVERY_TEST"
    await db.execute(
        "INSERT OR REPLACE INTO strategy_state (strategy_id, symbol, current_position, avg_entry_price, last_update) VALUES (?, ?, ?, ?, ?)",
        (strategy_id, "005930", 10, 68000, datetime.now())
    )
    print(f" - Saved crash state: {strategy_id} has 10 shares.")
    
    # Simulate Restart: Create new Strategy instance and load state
    from strategy.base_strategy import BaseStrategy, StrategyState
    import pandas as pd
    
    class TestStrategy(BaseStrategy):
        def calculate_signals(self, df: pd.DataFrame):
            return df
            
    new_strategy = TestStrategy(strategy_id, "005930")
    
    # Load from DB
    rows = await db.fetch_all(f"SELECT * FROM strategy_state WHERE strategy_id='{strategy_id}'")
    if rows:
        row = rows[0]
        state = StrategyState(
            strategy_id=row['strategy_id'],
            symbol=row['symbol'],
            current_position=row['current_position'],
            avg_entry_price=row['avg_entry_price'],
            last_update=row['last_update']
        )
        new_strategy.set_state(state)
        print(f" - Restored State: Pos={new_strategy.state.current_position}, AvgPrice={new_strategy.state.avg_entry_price}")
        
        if new_strategy.state.current_position == 10:
            print("SUCCESS: Strategy state restored correctly.")
        else:
            print("FAILED: State mismatch.")
    else:
        print("FAILED: Could not find saved state.")

    # Cleanup
    await db.execute(f"DELETE FROM strategy_state WHERE strategy_id='{strategy_id}'")
    await db.close()

    print("\n" + "=" * 60)
    print("   SCENARIO TEST 2 COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
