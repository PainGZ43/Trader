import sys
import os
import asyncio
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from execution.order_manager import OrderManager
from data.kiwoom_rest_client import KiwoomRestClient
from execution.notification import NotificationManager
from core.logger import get_logger
from strategy.base_strategy import Signal
from datetime import datetime

# Setup Logger to capture output
# setup_logger() # Not needed, auto-init
logger = get_logger("VerifyScenario")

async def run_scenario():
    logger.info("--- Starting Buy/Sell Scenario Verification ---")
    
    # 1. Initialize Mock Client
    kiwoom = KiwoomRestClient()
    # Force Mock Mode for safety if not already
    kiwoom.is_mock_server = True 
    
    # 2. Initialize Notification Manager
    nm = NotificationManager()
    await nm.start()
    
    # 3. Initialize OrderManager with Notification
    om = OrderManager(kiwoom, notification_manager=nm)
    await om.initialize()
    
    # 4. Scenario: Buy Samsung Electronics
    logger.info("[Scenario 1] Buying Samsung Elec (005930)...")
    buy_signal = Signal(symbol="005930", type="BUY", price=70000, timestamp=datetime.now(), reason="Test Buy")
    order_id = await om.send_order(buy_signal, 10, "12345678")
    
    if order_id:
        logger.info(f"Buy Order Placed. ID: {order_id}")
        
        # Simulate Fill Event
        logger.info("Simulating FILL Event...")
        event_data = {
            'order_no': order_id,
            'status': 'FILLED',
            'code': '005930',
            'qty': 10,
            'exec_qty': 10,
            'price': 70000
        }
        await om.on_order_event(event_data)
        
    else:
        logger.error("Buy Order Failed.")
        
    # 5. Wait for notifications to be sent
    await asyncio.sleep(2)
    await nm.stop()
    
    logger.info("--- Scenario Complete ---")

if __name__ == "__main__":
    asyncio.run(run_scenario())
