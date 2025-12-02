import sys
import os
import asyncio
from unittest.mock import MagicMock, AsyncMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.logger import get_logger
logger = get_logger("Rate_Verification")

async def verify_kiwoom_rate():
    logger.info("--- Verifying Kiwoom Exchange Rate Logic ---")
    try:
        from data.macro_collector import macro_collector
        
        # Mock rest_client
        macro_collector.rest_client = MagicMock()
        
        # Scenario 1: Successful Fetch (Price 14670 -> Rate 1467.0)
        macro_collector.rest_client.get_current_price = AsyncMock(return_value={
            "output": {"price": "14,670"}
        })
        
        await macro_collector.update_exchange_rate()
        
        if macro_collector.exchange_rate == 1467.0:
            logger.info(f"✅ Rate Calculation Correct: 14670 -> {macro_collector.exchange_rate}")
        else:
            logger.error(f"❌ Rate Calculation Failed: Expected 1467.0, Got {macro_collector.exchange_rate}")
            return False
            
        # Scenario 2: Zero Price
        macro_collector.rest_client.get_current_price = AsyncMock(return_value={
            "output": {"price": "0"}
        })
        # Should keep previous value or handle gracefully
        # Here we just check it doesn't crash
        await macro_collector.update_exchange_rate()
        logger.info("✅ Handled Zero Price gracefully")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Verification Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    success = loop.run_until_complete(verify_kiwoom_rate())
    
    if success:
        logger.info("KIWOOM RATE LOGIC VERIFIED.")
        sys.exit(0)
    else:
        logger.error("KIWOOM RATE LOGIC FAILED.")
        sys.exit(1)
