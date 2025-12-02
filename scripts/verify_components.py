import sys
import os
import asyncio
from PyQt6.QtWidgets import QApplication

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.logger import get_logger
logger = get_logger("Verification")

def verify_header_bar():
    logger.info("Verifying HeaderBar...")
    try:
        app = QApplication(sys.argv)
        from ui.widgets.header_bar import HeaderBar
        header = HeaderBar()
        if not hasattr(header, 'kospi_label'):
            raise AttributeError("Missing kospi_label")
        if not hasattr(header, 'usd_label'):
            raise AttributeError("Missing usd_label for Exchange Rate")
        logger.info("✅ HeaderBar instantiated successfully.")
        return True
    except Exception as e:
        logger.error(f"❌ HeaderBar verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_macro_collector():
    logger.info("Verifying MacroCollector...")
    try:
        from data.macro_collector import macro_collector
        # Check for critical methods
        if not hasattr(macro_collector, 'update_market_indices'):
            raise AttributeError("Missing update_market_indices")
        if not hasattr(macro_collector, 'update_exchange_rate'):
            raise AttributeError("Missing update_exchange_rate")
        if not hasattr(macro_collector, 'on_realtime_data'):
            raise AttributeError("Missing on_realtime_data")
        
        logger.info("✅ MacroCollector structure verified.")
        return True
    except Exception as e:
        logger.error(f"❌ MacroCollector verification failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting Component Verification...")
    
    v1 = verify_macro_collector()
    v2 = verify_header_bar()
    
    if v1 and v2:
        logger.info("ALL COMPONENTS VERIFIED SUCCESSFULLY.")
        sys.exit(0)
    else:
        logger.error("VERIFICATION FAILED.")
        sys.exit(1)
