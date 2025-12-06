import asyncio
import sys
import os
sys.path.append(os.getcwd())

from data.kiwoom_rest_client import kiwoom_client
from core.logger import get_logger
from datetime import datetime

async def test_fetch():
    logger = get_logger("TestKiwoom")
    
    # 1. Check Token (Reuse existing if valid)
    token = await kiwoom_client.get_token()
    if not token:
        print("Failed to get token.")
        return
        
    print(f"Token: {token[:10]}...")
    
    # 2. Test Correct Endpoint
    symbol = "005930"
    end_date = datetime.now().strftime("%Y%m%d")
    
    endpoint = "/api/dostk/chart"
    api_id = "ka10081"
    
    print(f"\nTesting {endpoint} with ID {api_id}")
    
    data = {
        "stk_cd": symbol,
        "base_dt": end_date,
        "upd_stkpc_tp": "1" # 1: Day?
    }
    
    resp = await kiwoom_client.request("POST", endpoint, data=data, api_id=api_id)
    
    if resp:
        code = resp.get('rt_cd') or resp.get('return_code')
        msg = resp.get('msg1') or resp.get('return_msg')
        print(f"Code: {code}, Msg: {msg}")
        
        if str(code) == '0':
            print("SUCCESS!!!")
            if "stk_dt_pole_chart_qry" in resp:
                print(f"Data Count: {len(resp['stk_dt_pole_chart_qry'])}")
                print(f"First Row: {resp['stk_dt_pole_chart_qry'][0]}")
        else:
            print(f"Full Response: {resp}")
    else:
        print("No response.")

    await kiwoom_client.close()

if __name__ == "__main__":
    asyncio.run(test_fetch())
