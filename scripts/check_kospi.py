import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data.kiwoom_rest_client import kiwoom_client
from core.logger import get_logger

# Configure logger to print to console
import logging
logging.basicConfig(level=logging.INFO)

async def check_kospi():
    print("Fetching KOSPI from Kiwoom...")
    try:
        # KOSPI Code: 001
        data = await kiwoom_client.get_market_index("001")
        
        if data and "output" in data:
            price = data["output"].get("price", "Unknown")
            change = data["output"].get("change", "Unknown")
            print(f"Current KOSPI: {price} (Change: {change})")
        else:
            print("Failed to fetch KOSPI data.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await kiwoom_client.close()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check_kospi())
