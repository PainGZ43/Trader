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
logger = get_logger("ScenarioTest_1_Retry")
logging.basicConfig(level=logging.INFO)

async def main():
    print("=" * 60)
    print("   SCENARIO TEST 1: RETRY ORDER (BRUTE FORCE TR ID)")
    print("=" * 60)

    # 1. Setup: Register Key
    print("\n[Step 1] Setting up Test Key...")
    try:
        existing = key_manager.get_keys()
        for k in existing:
            if k['account_no'] == test_config.MOCK_ACCOUNT:
                key_manager.delete_key(k['uuid'])

        success = await key_manager.add_key(
            owner="ScenarioTest",
            key_type="MOCK",
            account_no=test_config.MOCK_ACCOUNT,
            app_key=test_config.MOCK_APP_KEY,
            secret_key=test_config.MOCK_SECRET_KEY,
            expiry_date="20251231"
        )
        
        if success:
            keys = key_manager.get_keys()
            target_uuid = next((k['uuid'] for k in keys if k['account_no'] == test_config.MOCK_ACCOUNT), None)
            if target_uuid:
                key_manager.set_active_key(target_uuid)
                print(" - Test Key Activated.")
            else:
                return
        else:
            return

    except Exception as e:
        print(f" - Setup Failed: {e}")
        return

    # 2. Initialize Kiwoom Client
    print("\n[Step 2] Initializing Kiwoom Client...")
    kiwoom_client.offline_mode = False 
    kiwoom_client.is_mock_server = True
    
    token = await kiwoom_client.get_token()
    if token:
        print(f" - Login Successful. Token: {token[:10]}...")
    else:
        print(" - Login Failed. Cannot proceed with Remote Order test.")
        return

    # 3. Buy Order with Correct TR ID (via Client)
    symbol = "005930" # Samsung Elec
    qty = 1
    
    print(f"\n[Step 3] Attempting Buy Order via Client (Mock TR ID: kt10000)...")
    
    # Send Buy Order
    res = await kiwoom_client.send_order(symbol, "1", qty, 0, "03") # Market Buy
    print(f"   Result: {res}")
    
    # Initialize Notification Manager
    from execution.notification import NotificationManager
    notification_manager = NotificationManager()
    notification_manager.logger.setLevel("DEBUG") # Enable DEBUG logging
    await notification_manager.start() # Start background worker
    
    # Check for success (Mock returns return_code: 0, Real might return rt_cd: 0)
    # Also allow return_code 20 (Market Closed) for notification testing
    is_success = False
    if res:
        rc = str(res.get("return_code"))
        rt = str(res.get("rt_cd"))
        if rc == "0" or rt == "0":
            is_success = True
        elif rc == "20": # Market Closed
            print("   [NOTE] Market Closed. Simulating success for Notification Test.")
            is_success = True
            
    if is_success:
        ord_no = res.get('ord_no') or res.get('output', {}).get('order_no') or "TEST_ORD_NO"
        print(f"   SUCCESS! Order Sent. ID: {ord_no}")
        
        # Send Notification
        # Premium Spec:
        # 🚀 [매수 체결]
        # 종목명 (종목번호)
        #
        # • 체결가: 000원
        # • 수량: 00주
        # • 총액: 000원
        # • 전략: ????
        total_amt = int(qty) * 0 
        msg = (
            f"🚀 [매수 체결]\n"
            f"{symbol} ({symbol})\n\n"
            f"• 체결가: 0원\n"
            f"• 수량: {qty}주\n"
            f"• 총액: {total_amt}원\n"
            f"• 전략: ScenarioTest"
        )
        await notification_manager.send_message(msg)
        print("   Notification Queued.")
        
        # 3.1 Sell Order (kt10001)
        await asyncio.sleep(1)
        print(f"\n[Step 3.1] Attempting Sell Order via Client (Mock TR ID: kt10001)...")
        res_sell = await kiwoom_client.send_order(symbol, "2", qty, 0, "03") # Market Sell
        print(f"   Result: {res_sell}")
        
        is_sell_success = False
        if res_sell:
            rc = str(res_sell.get("return_code"))
            rt = str(res_sell.get("rt_cd"))
            if rc == "0" or rt == "0":
                is_sell_success = True
            elif rc == "20": # Market Closed
                is_sell_success = True
                
        if is_sell_success:
             print(f"   SUCCESS! Sell Order Sent.")
             
             # Send Sell Notification
             sell_ord_no = res_sell.get('ord_no') or res_sell.get('output', {}).get('order_no')
             msg_sell = (
                f"💰 [매도 체결]\n"
                f"{symbol} ({symbol})\n\n"
                f"• 체결가: 0원\n"
                f"• 수량: {qty}주\n"
                f"• 실현손익: 0원 (0.00%)\n"
                f"• 전략: ScenarioTest"
             )
             await notification_manager.send_message(msg_sell)
             print("   Sell Notification Queued.")
             
    elif res and "1504" in str(res):
        print("   Failed: API ID not supported.")
    else:
        print("   Failed: Other error.")

    # Wait for notifications to be sent
    print("   Waiting for notifications to be sent...")
    await notification_manager.wait_all_sent()
    await notification_manager.stop()
    print("   Notification Manager Stopped.")

    # 4. Teardown
    print("\n[Step 4] Teardown...")
    active_key = key_manager.get_active_key()
    if active_key:
        key_manager.delete_key(active_key['uuid'])
            
    from core.secure_storage import secure_storage
    secure_storage.delete(f"API_KEY_{active_key['uuid']}")

    print("\n" + "=" * 60)
    print("   TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
