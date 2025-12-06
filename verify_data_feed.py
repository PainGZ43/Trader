import sys
import os
import asyncio
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.kiwoom_rest_client import kiwoom_client
from data.key_manager import key_manager

async def verify_data():
    print("Starting Data Feed Verification...")
    
    # 1. Check Active Key
    active_key = key_manager.get_active_key()
    if not active_key:
        print("[FAIL] No active API key found. Please register a key first.")
        return

    print(f"Active Key: {active_key.get('owner')} ({active_key.get('type')})")
    
    # 2. Get Token
    print("Requesting Access Token...")
    token = await kiwoom_client.get_token()
    if not token:
        print("[FAIL] Failed to issue Access Token.")
        return
    print(f"[PASS] Token issued: {token[:10]}...")

    # 3. Fetch Stock Price (Samsung Electronics: 005930)
    print("Fetching Current Price for 005930 (Samsung Electronics)...")
    price_data = await kiwoom_client.get_current_price("005930")
    if price_data:
        print(f"[PASS] Price Data Received: {json.dumps(price_data, indent=2, ensure_ascii=False)}")
    else:
        print("[FAIL] Failed to fetch price data.")

    # 4. Fetch Market Index (KOSPI: 001)
    print("Fetching KOSPI Index...")
    index_data = await kiwoom_client.get_market_index("001")
    if index_data:
        print(f"[PASS] Index Data Received: {json.dumps(index_data, indent=2, ensure_ascii=False)}")
    else:
        print("[FAIL] Failed to fetch index data.")

    await kiwoom_client.close()

if __name__ == "__main__":
    asyncio.run(verify_data())
