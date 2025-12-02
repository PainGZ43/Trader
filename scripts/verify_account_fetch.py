import sys
import os
import asyncio
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.logger import get_logger
from data.kiwoom_rest_client import kiwoom_client
from execution.account_manager import AccountManager
from core.config import config

logger = get_logger("VerifyAccount")

async def verify_account():
    logger.info("--- Verifying Account Fetch Logic ---")
    
    # Check current mode
    is_mock = config.get("MOCK_MODE", True)
    logger.info(f"Current Mode: {'MOCK' if is_mock else 'REAL'}")
    
    # Mock Exchange for AccountManager (it expects an object with get_account_balance)
    # But here we can use kiwoom_client directly if we pass it to AccountManager
    
    am = AccountManager(kiwoom_client)
    
    try:
        # 1. Test KiwoomRestClient directly
        logger.info("1. Testing KiwoomRestClient.get_account_balance()...")
        raw_res = await kiwoom_client.get_account_balance()
        print(f"\n[RAW RESULT] {json.dumps(raw_res, indent=2, ensure_ascii=False)}\n")
        
        if not raw_res:
            logger.error("Failed to fetch raw balance.")
            return False
            
        # 2. Test AccountManager.update_balance()
        logger.info("2. Testing AccountManager.update_balance()...")
        await am.update_balance()
        
        summary = am.get_summary()
        balance = summary["balance"]
        positions = summary["positions"]
        
        print(f"\n[PARSED BALANCE] {json.dumps(balance, indent=2, ensure_ascii=False)}")
        print(f"[PARSED POSITIONS] {len(positions)} items")
        
        if balance["total_asset"] > 0:
            logger.info(f"[OK] Account Fetch Verified. Asset: {balance['total_asset']:,.0f}")
            return True
        else:
            logger.error("[FAIL] Account Fetch Failed: Total Asset is 0 or missing.")
            return False
            
    except Exception as e:
        logger.error(f"Error verifying account: {e}")
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
    
    loop.run_until_complete(verify_account())
