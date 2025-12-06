import asyncio
import sys
import os
sys.path.append(os.getcwd())

from data.kiwoom_rest_client import kiwoom_client
from core.logger import get_logger
from datetime import datetime, timedelta

async def test_fetch():
    logger = get_logger("TestKiwoom")
    
    # 0. Clear Token Storage to force new issuance
    from core.secure_storage import secure_storage
    print("Clearing stored token...")
    secure_storage.delete("kiwoom_access_token")
    secure_storage.delete("kiwoom_token_expiry")
    
    # 1. Check Token
    token = await kiwoom_client.get_token()
    if not token:
        print("Failed to get token.")
        return
        
    print(f"Token: {token[:10]}...")
    
    # 2. Probe API IDs
    symbol = "005930"
    end_date = datetime.now().strftime("%Y%m%d")
    
    endpoints = ["/api/dostk/ohlcv_day", "/api/dostk/ohlcv", "/api/dostk/chart"]
    api_ids = ["GetOHLCV", "GetDailyPrice", "GetStockChart", "GetChart", "GetPrice", "opt10081", "ka10005", "ka10001"]
    
    for ep in endpoints:
        for aid in api_ids:
            print(f"\nTesting {ep} with ID {aid}")
            data = {
                "stk_cd": symbol,
                "date": end_date,
                "tick": "1"
            }
            resp = await kiwoom_client.request("POST", ep, data=data, api_id=aid)
            
            if resp:
                code = resp.get('rt_cd') or resp.get('return_code')
                msg = resp.get('msg1') or resp.get('return_msg')
                print(f"Code: {code}, Msg: {msg}")
                
                if str(code) == '0':
                    print(f"SUCCESS!!! Found: {ep} with {aid}")
                    return
            else:
                print("No response.")

    await kiwoom_client.close()

if __name__ == "__main__":
    asyncio.run(test_fetch())
