import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.kiwoom_rest_client import kiwoom_client

async def verify_auth():
    print("=== Kiwoom REST API Authentication Verification ===")
    
    # 1. Test Real Server Mode
    print("\n[1] Testing Authentication (Real Server Mode)...")
    kiwoom_client.is_mock_server = False
    kiwoom_client.offline_mode = False
    kiwoom_client.base_url = kiwoom_client.BASE_URL_REAL
    
    token = await kiwoom_client.get_token()
    if token:
        print(f"SUCCESS: Token Issued (Real): {token[:10]}...")
        await kiwoom_client.revoke_token()
    else:
        print("FAILED: Token Issuance Failed (Real).")

    # 2. Test Mock Server Mode
    print("\n[2] Testing Authentication (Mock Server Mode)...")
    kiwoom_client.is_mock_server = True
    kiwoom_client.base_url = kiwoom_client.BASE_URL_MOCK
    
    # Reset session/token for new test
    kiwoom_client.access_token = None
    if kiwoom_client.session:
        await kiwoom_client.session.close()
        kiwoom_client.session = None
        
    token = await kiwoom_client.get_token()
    if token:
        print(f"SUCCESS: Token Issued (Mock): {token[:10]}...")
        await kiwoom_client.revoke_token()
    else:
        print("FAILED: Token Issuance Failed (Mock).")
    
    await kiwoom_client.close()

if __name__ == "__main__":
    asyncio.run(verify_auth())
