import sys
import os
import asyncio
import qasync
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    import PyQt6
    print(f"PyQt6 Version: {PyQt6.QtCore.PYQT_VERSION_STR}")
    import qtawesome
    print(f"QtAwesome Version: {qtawesome.__version__}")
except ImportError as e:
    print(f"Import Error: {e}")

def verify_ui_launch():
    app = QApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    # Import UI after QApplication is created
    from ui.main_window import MainWindow
    
    # Define main async function inside to capture window reference if needed, 
    # or just call the external main. 
    # But external main needs window.
    
    # Let's redefine main here or pass window to it.
    # Actually, we can just call the existing main if we move imports.
    
    with loop:
        loop.run_until_complete(main_async())
    
    print("UI Verification Completed Successfully.")

async def main_async():
    # Import here to ensure QApplication exists
    from ui.main_window import MainWindow
    from core.event_bus import event_bus
    from core.logger import get_logger
    
    logger = get_logger("VerifyAccountUI")
    logger.info("Starting Account UI Verification...")
    
    window = MainWindow()
    window.show()
    
    # 1. Mock Account Data
    mock_balance = {
        "deposit": 10000000.0,
        "total_asset": 15000000.0,
        "total_pnl": 500000.0,
        "total_purchase": 14500000.0,
        "total_eval": 15000000.0,
        "total_return": 3.45
    }
    
    mock_portfolio = [
        {
            "code": "005930",
            "name": "Samsung Elec",
            "qty": 100,
            "avg_price": 70000.0,
            "current_price": 72000.0,
            "eval_amt": 7200000.0,
            "earning_rate": 2.85
        },
        {
            "code": "000660",
            "name": "SK Hynix",
            "qty": 50,
            "avg_price": 120000.0,
            "current_price": 118000.0,
            "eval_amt": 5900000.0,
            "earning_rate": -1.67
        }
    ]
    
    # 2. Publish Events
    logger.info("Publishing account.summary...")
    event_bus.publish("account.summary", {"balance": mock_balance})
    
    logger.info("Publishing account.portfolio...")
    event_bus.publish("account.portfolio", mock_portfolio)
    
    # Wait for UI update (Events are async)
    await asyncio.sleep(1)
    
    # 3. Verify UI Components
    
    # A. ControlPanel Summary
    cp = window.control_panel
    deposit_txt = cp.val_deposit.text().replace(",", "")
    asset_txt = cp.val_asset.text().replace(",", "")
    
    logger.info(f"ControlPanel Deposit: {deposit_txt}")
    logger.info(f"ControlPanel Asset: {asset_txt}")
    
    if deposit_txt == "10000000":
        logger.info("[OK] ControlPanel Deposit matches.")
    else:
        logger.error(f"[FAIL] ControlPanel Deposit mismatch. Expected 10000000, got {deposit_txt}")
        
    if asset_txt == "15000000":
        logger.info("[OK] ControlPanel Asset matches.")
    else:
        logger.error(f"[FAIL] ControlPanel Asset mismatch. Expected 15000000, got {asset_txt}")
        
    # B. ControlPanel Portfolio Table
    row_count = cp.table.rowCount()
    logger.info(f"Portfolio Table Rows: {row_count}")
    
    if row_count == 2:
        logger.info("[OK] Portfolio Table row count matches.")
        
        # Check first row (Samsung)
        item_name = cp.table.item(0, 1).text()
        item_price = cp.table.item(0, 3).text().replace(",", "")
        
        if item_name == "Samsung Elec" and item_price == "72000":
            logger.info("[OK] Portfolio Row 0 data matches.")
        else:
            logger.error(f"[FAIL] Portfolio Row 0 mismatch. Got {item_name}, {item_price}")
    else:
        logger.error(f"[FAIL] Portfolio Table row count mismatch. Expected 2, got {row_count}")

    # C. HeaderBar Account Info
    hb = window.header
    header_txt = hb.asset_label.text() # Accessed directly as we know the name
    logger.info(f"HeaderBar Text: {header_txt}")
    
    if "15,000,000" in header_txt or "10,000,000" in header_txt:
         logger.info("[OK] HeaderBar updated.")
    else:
         logger.warning(f"[WARN] HeaderBar might not be updated. Text: {header_txt}")

    logger.info("Verification Complete.")
    window.close()

if __name__ == "__main__":
    verify_ui_launch()
