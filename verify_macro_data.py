import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.macro_collector import macro_collector
from data.kiwoom_rest_client import kiwoom_client
from core.logger import get_logger

logger = get_logger("VERIFY_MACRO")

async def verify_macro():
    print("=== Verifying Macro Data Collection ===")
    
    # 1. Test KiwoomRestClient.get_market_index directly
    print("\n[1] Testing KiwoomRestClient.get_market_index...")
    
    # Mock Mode Check
    print(f"Client Mode: {'MOCK' if kiwoom_client.is_mock_server else 'REAL'}")
    
    kospi = await kiwoom_client.get_market_index("001")
    print(f"KOSPI Raw: {kospi}")
    
    kosdaq = await kiwoom_client.get_market_index("101")
    print(f"KOSDAQ Raw: {kosdaq}")
    
    # 2. Test MacroCollector.update_market_indices
    print("\n[2] Testing MacroCollector.update_market_indices...")
    await macro_collector.update_market_indices()
    print(f"Collector Indices: {macro_collector.indices}")
    
    if macro_collector.indices["KOSPI"] > 0 and macro_collector.indices["KOSDAQ"] > 0:
        print("✅ Indices Update Success")
    else:
        print("❌ Indices Update Failed")

    # 3. Test MacroCollector.update_exchange_rate
    print("\n[3] Testing MacroCollector.update_exchange_rate...")
    await macro_collector.update_exchange_rate()
    print(f"Collector Exchange Rate: {macro_collector.exchange_rate}")
    
    if macro_collector.exchange_rate > 0:
        print("✅ Exchange Rate Update Success")
    else:
        print("❌ Exchange Rate Update Failed")
        
    print("\n=== Verification Complete ===")

if __name__ == "__main__":
    asyncio.run(verify_macro())
