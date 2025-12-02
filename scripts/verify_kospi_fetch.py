import sys
import os
import asyncio
from unittest.mock import MagicMock, AsyncMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.logger import get_logger
logger = get_logger("KOSPI_Verification")

async def verify_kospi_fetch():
    logger.info("--- Verifying KOSPI Fetch Logic ---")
    try:
        from data.macro_collector import macro_collector
        
        # Mock rest_client
        macro_collector.rest_client = MagicMock()
        
        # Scenario: Successful Fetch
        macro_collector.rest_client.get_market_index = AsyncMock(return_value={
            "output": {"price": "2,500.50"}
        })
        
        await macro_collector.update_market_indices()
        
        if macro_collector.indices["KOSPI"] == 2500.50:
            logger.info(f"✅ KOSPI Fetch Correct: 2500.50")
        else:
            logger.error(f"❌ KOSPI Fetch Failed: Expected 2500.50, Got {macro_collector.indices['KOSPI']}")
            return False
            
        # Verify call arguments
        macro_collector.rest_client.get_market_index.assert_called_with("001")
        logger.info("✅ Called get_market_index('001') correctly")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Verification Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    success = loop.run_until_complete(verify_kospi_fetch())
    
    if success:
        logger.info("KOSPI FETCH LOGIC VERIFIED.")
        sys.exit(0)
    else:
        logger.error("KOSPI FETCH LOGIC FAILED.")
        sys.exit(1)
