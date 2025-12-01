import asyncio
import sys
import os
import logging
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.logger import get_logger
from core.config import config
from data.kiwoom_rest_client import kiwoom_client
from data.key_manager import key_manager
import scripts.scenario_config as test_config

# Configure logging
sys.stdout.reconfigure(encoding='utf-8')
logger = get_logger("ScenarioTest_1")
logging.basicConfig(level=logging.INFO)

async def main():
    print("=" * 60)
    print("   SCENARIO TEST 1: NORMAL OPERATION")
    print("=" * 60)

    # 1. Setup: Register Key
    print("\n[Step 1] Setting up Test Key...")
    try:
        # Check if key already exists (cleanup might have failed)
        existing = key_manager.get_keys()
        for k in existing:
            if k['account_no'] == test_config.MOCK_ACCOUNT:
                print(f" - Found existing test key ({k['uuid']}), removing it first.")
                key_manager.delete_key(k['uuid'])

        # Add Key
        success = await key_manager.add_key(
            owner="ScenarioTest",
            key_type="MOCK",
            account_no=test_config.MOCK_ACCOUNT,
            app_key=test_config.MOCK_APP_KEY,
            secret_key=test_config.MOCK_SECRET_KEY,
            expiry_date="20251231" # Dummy expiry
        )
        
        if success:
            print(" - Test Key Registered Successfully.")
            # Set Active
            keys = key_manager.get_keys()
            target_uuid = next((k['uuid'] for k in keys if k['account_no'] == test_config.MOCK_ACCOUNT), None)
            if target_uuid:
                key_manager.set_active_key(target_uuid)
                print(" - Test Key Activated.")
            else:
                print(" - Failed to find registered key UUID.")
                return
        else:
            print(" - Failed to register Test Key.")
            return

    except Exception as e:
        print(f" - Setup Failed: {e}")
        return

    # 2. Initialize Kiwoom Client
    print("\n[Step 2] Initializing Kiwoom Client...")
    # Try Remote Mode first since we have valid keys
    kiwoom_client.offline_mode = False 
    kiwoom_client.is_mock_server = True
    
    # Login
    token = await kiwoom_client.get_token()
    if token:
        print(f" - Login Successful. Token: {token[:10]}...")
    else:
        print(" - Login Failed. Switching to Offline Mode for logic verification.")
        kiwoom_client.offline_mode = True

    # 3. Balance Check
    print("\n[Step 3] Checking Balance...")
    balance = await kiwoom_client.get_account_balance()
    if balance:
        print(f" - Balance Retrieved: Deposit={balance.get('deposit', 'N/A')}")
        print(f" - Positions: {len(balance.get('positions', []))}")
    else:
        print(" - Failed to retrieve balance.")

    # 4. Buy Order
    symbol = "005930" # Samsung Elec
    qty = 1
    print(f"\n[Step 4] Sending Buy Order ({symbol}, {qty} shares)...")
    
    order_res = await kiwoom_client.send_order(symbol, "1", qty, 0, "03") # 1: Buy, 03: Market
    if order_res:
        print(f" - Buy Order Sent. Order No/ID: {order_res}")
    else:
        print(" - Buy Order Failed.")

    # Wait for execution simulation
    print(" - Waiting 3 seconds...")
    await asyncio.sleep(3)

    # 5. Sell Order
    print(f"\n[Step 5] Sending Sell Order ({symbol}, {qty} shares)...")
    # In real scenario, we need order_no for cancel, but for new sell order we just send sell
    # Sell is type "2"
    sell_res = await kiwoom_client.send_order(symbol, "2", qty, 0, "03")
    if sell_res:
        print(f" - Sell Order Sent. Order No/ID: {sell_res}")
    else:
        print(" - Sell Order Failed.")

    # 6. Teardown
    print("\n[Step 6] Teardown (Cleaning up keys)...")
    active_key = key_manager.get_active_key()
    if active_key:
        if key_manager.delete_key(active_key['uuid']):
            print(" - Test Key Deleted.")
        else:
            print(" - Failed to delete Test Key.")
            
    # Also clean from SecureStorage explicitly if needed, but delete_key should handle it
    from core.secure_storage import secure_storage
    secure_storage.delete(f"API_KEY_{active_key['uuid']}") # Double check

    print("\n" + "=" * 60)
    print("   SCENARIO TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
