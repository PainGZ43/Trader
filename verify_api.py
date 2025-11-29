import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.kiwoom_rest_client import kiwoom_client
from core.config import config

async def main():
    print("=== Kiwoom REST API Verification ===")
    
    # 1. Authentication
    print("\n[1] Testing Authentication (Offline Mode)...")
    
    # Use Offline Mode since keys are invalid
    kiwoom_client.offline_mode = True
    
    token = await kiwoom_client.get_token()
    print(f"Token: {token}")
    
    if not token:
        print("Authentication Failed!")
        return

    # 2. Market Data
    print("\n[2] Testing Market Data (Samsung Elec)...")
    price_data = await kiwoom_client.get_current_price("005930")
    print(f"Price Data: {price_data}")

    # 3. Account Balance
    print("\n[3] Testing Account Balance...")
    balance = await kiwoom_client.get_account_balance()
    print(f"Balance: {balance}")

    # 4. Order (Mock Mode)
    print("\n[4] Testing Order (Mock Mode)...")
    order = await kiwoom_client.send_order("005930", "1", "10", "0", "03") # Buy 10 Market
    print(f"Order Result: {order}")

    await kiwoom_client.close()

if __name__ == "__main__":
    asyncio.run(main())
