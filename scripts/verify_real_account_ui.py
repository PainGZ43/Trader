import sys
import os
import asyncio
import qasync
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def verify_ui_launch():
    app = QApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    with loop:
        loop.run_until_complete(main_async())
    
    print("Real Account UI Verification Completed.")

async def main_async():
    # Import here to ensure QApplication exists
    from ui.main_window import MainWindow
    from core.event_bus import event_bus
    from core.logger import get_logger
    from data.kiwoom_rest_client import kiwoom_client
    from execution.account_manager import AccountManager
    from data.key_manager import key_manager
    
    logger = get_logger("VerifyRealAccountUI")
    logger.info("Starting Real Account UI Verification...")
    
    # Check if API Key exists
    try:
        active_key = key_manager.get_active_key()
        if not active_key:
            logger.error("No active API key found! Please set API key in settings first.")
            return
        logger.info(f"Active Key Found: {active_key.get('app_key', 'N/A')[:4]}***")
    except Exception as e:
        logger.error(f"Error checking API key: {e}")
        return

    window = MainWindow()
    window.show()
    
    # Initialize AccountManager with Real Client
    account_manager = AccountManager(kiwoom_client)
    
    # Start Sync (This will fetch data from server)
    logger.info("Fetching Account Balance from Server...")
    try:
        # Add timeout
        await asyncio.wait_for(account_manager.update_balance(), timeout=10.0)
        logger.info("Account Balance Fetch Completed.")
    except asyncio.TimeoutError:
        logger.error("Timeout while fetching account balance!")
        window.close()
        return
    except Exception as e:
        logger.error(f"Failed to fetch balance: {e}")
        window.close()
        return
        
    # Wait for UI update (Events are async)
    await asyncio.sleep(2)
    
    # Verify UI Components
    
    # A. ControlPanel Summary
    cp = window.control_panel
    deposit_txt = cp.val_deposit.text()
    asset_txt = cp.val_asset.text()
    
    logger.info(f"ControlPanel Deposit: {deposit_txt}")
    logger.info(f"ControlPanel Asset: {asset_txt}")
    
    if deposit_txt != "0" and deposit_txt != "-":
        logger.info("[OK] ControlPanel Deposit updated.")
    else:
        logger.warning(f"[WARN] ControlPanel Deposit might be empty. Got {deposit_txt}")
        
    # B. ControlPanel Portfolio Table
    row_count = cp.table.rowCount()
    logger.info(f"Portfolio Table Rows: {row_count}")
    
    if row_count > 0:
        logger.info(f"[OK] Portfolio Table has {row_count} items.")
        # Log first item
        item_name = cp.table.item(0, 1).text()
        item_price = cp.table.item(0, 3).text()
        logger.info(f"First Item: {item_name} @ {item_price}")
    else:
        logger.info("[INFO] Portfolio is empty (No positions found).")

    # C. HeaderBar Account Info
    hb = window.header
    header_txt = hb.asset_label.text()
    logger.info(f"HeaderBar Text: {header_txt}")
    
    if "--" not in header_txt:
         logger.info("[OK] HeaderBar updated.")
    else:
         logger.warning(f"[WARN] HeaderBar might not be updated. Text: {header_txt}")

    logger.info("Verification Complete. Closing in 3 seconds...")
    await asyncio.sleep(3)
    window.close()

if __name__ == "__main__":
    verify_ui_launch()
