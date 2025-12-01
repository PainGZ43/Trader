import asyncio
import sys
import os
import logging
import aiohttp

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.logger import get_logger
import scripts.scenario_config as test_config

# Configure logging
sys.stdout.reconfigure(encoding='utf-8')
logger = get_logger("TestRealURL")
logging.basicConfig(level=logging.INFO)

async def main():
    print("=" * 60)
    print("   TEST REAL URL WITH MOCK CREDENTIALS")
    print("=" * 60)

    # Config
    APP_KEY = test_config.MOCK_APP_KEY
    SECRET_KEY = test_config.MOCK_SECRET_KEY
    ACCOUNT_NO = test_config.MOCK_ACCOUNT
    
    BASE_URL = "https://api.kiwoom.com" # Real Server
    
    print(f"Target URL: {BASE_URL}")
    print(f"App Key: {APP_KEY[:10]}...")
    
    # 1. Get Token
    print("\n[Step 1] Attempting Authentication...")
    url = f"{BASE_URL}/oauth2/token"
    headers = {
        "Content-Type": "application/json;charset=UTF-8"
    }
    data = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "secretkey": SECRET_KEY
    }
    
    token = None
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=headers, json=data) as response:
                print(f"   Status: {response.status}")
                if response.status == 200:
                    text = await response.text()
                    print(f"   Raw Response: {text}")
                    result = await response.json()
                    token = result.get("access_token")
                    print(f"   SUCCESS! Token: {token[:10]}...")
                else:
                    text = await response.text()
                    print(f"   FAILED. Response: {text}")
                    return
        except Exception as e:
            print(f"   Exception: {e}")
            return

    if not token:
        return

    # 2. Send Order (TT80012)
    print("\n[Step 2] Attempting Order (TT80012)...")
    endpoint = "/api/dostk/order"
    url = f"{BASE_URL}{endpoint}"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json;charset=UTF-8",
        "api-id": "TT80012" # Real Server ID
    }
    
    data = {
        "acc_no": ACCOUNT_NO,
        "order_type": "1", # Buy
        "stk_cd": "005930", # Samsung Elec
        "qty": "1",
        "price": "0",
        "trade_type": "03" # Market
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=headers, json=data) as response:
                print(f"   Status: {response.status}")
                result = await response.json()
                print(f"   Result: {result}")
                
                if result.get("rt_cd") == "0":
                    print("   SUCCESS! Order Placed.")
                else:
                    print("   FAILED to Place Order.")
                    
        except Exception as e:
            print(f"   Exception: {e}")

    print("\n" + "=" * 60)
    print("   TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
