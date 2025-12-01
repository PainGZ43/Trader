import asyncio
import logging
import sys
import os
from datetime import datetime

# Ensure project root is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.logger import get_logger
from core.config import config
from core.database import db
from core.event_bus import event_bus
from data.kiwoom_rest_client import kiwoom_client
from data.data_collector import data_collector
from execution.engine import ExecutionEngine
from execution.order_manager import OrderManager
from strategy.base_strategy import Signal

# Configure logging
# Force UTF-8 for Windows Console to avoid emoji errors
sys.stdout.reconfigure(encoding='utf-8')
logger = get_logger("VerifySystem")
logging.basicConfig(level=logging.INFO)

async def main():
    print("=" * 60)
    print("   PRECISE FULL SYSTEM INTEGRATION VERIFICATION")
    print("=" * 60)

    # 1. Initialize Core Components
    print("\n[Step 1] Initializing Core Components...")
    
    # Database
    await db.connect()
    print(" - Database: Connected")
    
    # Config
    config.set("MOCK_MODE", True) # Ensure Mock Mode
    print(" - Config: MOCK_MODE = True")

    # Kiwoom Client (Offline Mock)
    kiwoom_client.offline_mode = True
    kiwoom_client.is_mock_server = True
    print(" - Kiwoom Client: Offline Mock Mode Enabled")

    # 2. Initialize Modules
    print("\n[Step 2] Initializing Modules...")
    
    # Data Collector
    # We won't start the full loop, but we'll use its processing methods
    print(" - Data Collector: Ready")

    # Execution Engine
    engine = ExecutionEngine(kiwoom_client, mode="MOCK")
    await engine.initialize()
    print(" - Execution Engine: Initialized")

    # 3. Verify Data Flow (DataCollector -> EventBus)
    print("\n[Step 3] Verifying Data Flow...")
    
    received_data = []
    async def on_market_data(event):
        # EventBus passes an Event object, data is in event.data
        data = event.data if hasattr(event, 'data') else event
        received_data.append(data)
        print(f"   > EventBus Received: {data.get('code')} Price={data.get('price')}")

    event_bus.subscribe("market.data", on_market_data)

    # Simulate incoming data
    mock_data = {
        "code": "005930",
        "name": "Samsung Elec",
        "price": 70000,
        "volume": 1000,
        "timestamp": datetime.now().isoformat()
    }
    
    print(f" - Publishing mock data: {mock_data['code']}")
    event_bus.publish("market.data", mock_data)
    
    await asyncio.sleep(0.5)
    
    if received_data:
        print("SUCCESS: Data propagated through EventBus.")
    else:
        print("FAILED: Data not received via EventBus.")
        return

    # 4. Verify Order Execution Flow
    print("\n[Step 4] Verifying Order Execution Flow...")
    
    # Create a dummy signal
    signal = Signal(
        symbol="005930",
        type="BUY",
        price=70000,
        timestamp=datetime.now(),
        reason="Test Signal",
        score=1.0
    )
    
    print(f" - Generated Signal: {signal.type} {signal.symbol}")
    
    # Manually trigger order via Engine's OrderManager
    # Note: Engine usually listens to signals. We'll call send_order directly to verify the chain.
    
    # Need to set an active key first for OrderManager to work
    from data.key_manager import key_manager
    # Add a temporary mock key if none exists
    if not key_manager.get_active_key():
        await key_manager.add_key("SystemTest", "MOCK", "12345678", "mock_app", "mock_sec", "20251231")
        active = key_manager.get_keys()[0]
        key_manager.set_active_key(active['uuid'])
        print(" - Created and activated temporary mock key.")

    try:
        # Engine's execute_signal logic
        print(" - Executing Signal via Engine (Testing Notification Flow)...")
        
        # Mock Notification Manager's send_message to verify output
        original_send_message = engine.notification_manager.send_message
        
        async def mock_send_message(msg, level="INFO"):
            print(f"\n[MOCK NOTIFICATION] Level: {level}")
            print(msg)
            print("-" * 30)
            # Call original to actually send the message
            await original_send_message(msg, level) 
            
        engine.notification_manager.send_message = mock_send_message
        
        # Mock Kiwoom's send_order to simulate success even if market is closed
        # We need to patch the instance method on the engine's order_manager's kiwoom client
        # But engine.order_manager.kiwoom is the same object as kiwoom_client
        
        original_send_order = kiwoom_client.send_order
        
        async def mock_send_order(*args, **kwargs):
            print(f"   [MOCK KIWOOM] Sending Order: {args} {kwargs}")
            # Return a success-like response matching OrderManager expectations
            return {
                'rt_cd': '0', 
                'output': {
                    'order_no': 'TEST_ORD_12345'
                }
            }
            
        # Temporarily patch send_order
        kiwoom_client.send_order = mock_send_order

        # Execute Signal
        # We need to ensure account manager has data or risk manager will fail
        # Mock Account Manager data
        engine.account_manager.balance = {
            "deposit": 100000000,
            "total_asset": 100000000,
            "daily_pnl": 0
        }
        
        await engine.execute_signal(signal, 10)
        
        # Restore mocks
        kiwoom_client.send_order = original_send_order
        engine.notification_manager.send_message = original_send_message
            
    except Exception as e:
        print(f"FAILED: Order execution exception: {e}")
        import traceback
        traceback.print_exc()

    # 5. Verify Database Persistence
    print("\n[Step 5] Verifying Database Persistence...")
    # Check if we can write/read a trade log
    try:
        # Table is trade_history
        await db.execute(
            "INSERT INTO trade_history (strategy, symbol, side, price, quantity, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
            ("TEST_STRAT", "005930", "BUY", 70000, 10, datetime.now())
        )
        
        rows = await db.fetch_all("SELECT * FROM trade_history WHERE strategy='TEST_STRAT'")
        if rows:
            row = rows[0]
            print(f"SUCCESS: Trade log saved and retrieved. ID: {row['id']}")
        else:
            print("FAILED: Trade log not found.")
    except Exception as e:
        print(f"FAILED: Database operation error: {e}")

    # Wait for notifications
    print("\n[Step 5.1] Waiting for notifications to be sent...")
    await engine.notification_manager.wait_all_sent()

    # 6. Cleanup
    print("\n[Step 6] Cleaning up...")
    await engine.notification_manager.stop()
    await db.close()
    print("SUCCESS: System shutdown.")

    print("\n" + "=" * 60)
    print("   VERIFICATION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
