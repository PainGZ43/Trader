import sys
import os
import asyncio
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.logger import get_logger
from data.kiwoom_rest_client import kiwoom_client
from core.config import config

logger = get_logger("FetchKOSPI")

async def fetch_kospi():
    logger.info("--- Fetching KOSPI Data from Kiwoom (Updated) ---")
    
    # Check current mode
    is_mock = config.get("MOCK_MODE", True)
    logger.info(f"Current Mode: {'MOCK' if is_mock else 'REAL'}")
    
    try:
        # Fetch KOSPI (001)
        # Now uses ka10004 with mrkt_tp="1"
        result = await kiwoom_client.get_market_index("001")
        
        print(f"\n[RAW RESULT] {json.dumps(result, indent=2, ensure_ascii=False)}\n")
        
        if result:
            # Handle potential different structures
            if "inds_netprps" in result:
                # Structure from PDF
                items = result["inds_netprps"]
                if items:
                    item = items[0]
                    name = item.get("inds_nm")
                    price = item.get("cur_prc")
                    change = item.get("flu_rt") # or pred_pre
                    
                    print(f"[PARSED] Name: {name}")
                    print(f"[PARSED] Price: {price}")
                    print(f"[PARSED] Change: {change}")
                    return True
            elif "output" in result:
                # Structure from Mock/Previous assumption
                output = result["output"]
                price = output.get("price", "N/A")
                print(f"[PARSED] Price: {price}")
                return True
            
        logger.error("Failed to parse result.")
        return False
            
    except Exception as e:
        logger.error(f"Error fetching KOSPI: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await kiwoom_client.close()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    loop.run_until_complete(fetch_kospi())
