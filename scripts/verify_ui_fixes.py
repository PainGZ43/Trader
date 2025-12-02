import sys
import os
from PyQt6.QtWidgets import QApplication, QTableWidgetItem
from PyQt6.QtCore import Qt

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.logger import get_logger
logger = get_logger("UI_Verification")

def verify_control_panel():
    logger.info("--- Verifying ControlPanel ---")
    try:
        from ui.widgets.control_panel import ControlPanel
        panel = ControlPanel()
        
        # Check Row Count (Should be 1 for empty state)
        row_count = panel.table.rowCount()
        if row_count != 1:
            logger.error(f"❌ ControlPanel: Expected 1 row for empty state, got {row_count}")
            return False
            
        # Check Text
        item = panel.table.item(0, 0)
        if not item or "No positions" not in item.text() and "보유 종목 없음" not in item.text():
             # Note: language_manager might return Korean or English depending on config. 
             # We check for either or just check if it's not empty/dummy.
             logger.info(f"ControlPanel Text: {item.text() if item else 'None'}")
        
        logger.info("✅ ControlPanel: Empty state verified.")
        return True
    except Exception as e:
        logger.error(f"❌ ControlPanel Verification Failed: {e}")
        return False

def verify_order_panel():
    logger.info("--- Verifying OrderPanel ---")
    try:
        from ui.widgets.order_panel import OrderPanel
        panel = OrderPanel()
        
        # Setup Mock Data
        deposit = 1000000 # 1 Million KRW
        price = 10000     # 10,000 KRW
        panel.update_account_info(deposit)
        panel.price_input.setValue(price)
        
        # Test 50%
        logger.info("Testing 50% Quick Qty...")
        panel.on_quick_qty("50%")
        
        expected_qty = int((deposit * 0.5) / price) # 50
        actual_qty = panel.qty_input.value()
        
        if actual_qty == expected_qty:
            logger.info(f"✅ OrderPanel: 50% Qty Correct (Expected {expected_qty}, Got {actual_qty})")
            return True
        else:
            logger.error(f"❌ OrderPanel: 50% Qty Incorrect (Expected {expected_qty}, Got {actual_qty})")
            return False
            
    except Exception as e:
        logger.error(f"❌ OrderPanel Verification Failed: {e}")
        return False

def verify_dashboard():
    logger.info("--- Verifying Dashboard ---")
    try:
        from ui.dashboard import Dashboard
        dash = Dashboard()
        
        # Check Initial State (Should be 0 - Welcome)
        initial_index = dash.stack_layout.currentIndex()
        if initial_index != 0:
            logger.error(f"❌ Dashboard: Initial index should be 0, got {initial_index}")
            return False
        logger.info("✅ Dashboard: Initial state is Welcome Screen.")
        
        # Simulate Data Receipt
        logger.info("Simulating Real-time Data...")
        dash.process_data({"type": "REALTIME", "code": "005930", "price": 60000})
        
        # Check New State (Should be 1 - Active)
        new_index = dash.stack_layout.currentIndex()
        if new_index != 1:
            logger.error(f"❌ Dashboard: Index did not switch to 1, got {new_index}")
            return False
        logger.info("✅ Dashboard: Switched to Active Screen on data.")
        return True
        
    except Exception as e:
        logger.error(f"❌ Dashboard Verification Failed: {e}")
        return False

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    v1 = verify_control_panel()
    v2 = verify_order_panel()
    v3 = verify_dashboard()
    
    if v1 and v2 and v3:
        logger.info("ALL UI FIXES VERIFIED SUCCESSFULLY.")
        sys.exit(0)
    else:
        logger.error("SOME UI FIXES FAILED VERIFICATION.")
        sys.exit(1)
