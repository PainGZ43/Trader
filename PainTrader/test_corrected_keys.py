import asyncio
import aiohttp
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_key(app_key, secret_key):
    print("=== Testing Corrected Keys ===")
    print(f"App Key: {app_key}")
    print(f"Secret Key: {secret_key}")
    
    servers = [
        {"name": "MOCK SERVER", "url": "https://mockapi.kiwoom.com"},
        {"name": "REAL SERVER", "url": "https://api.kiwoom.com"}
    ]
    
    async with aiohttp.ClientSession() as session:
        for server in servers:
            url = f"{server['url']}/oauth2/token"
            headers = {"Content-Type": "application/json;charset=UTF-8"}
            data = {
                "grant_type": "client_credentials",
                "appkey": app_key,
                "secretkey": secret_key
            }
            
            print(f"\nTesting against {server['name']}...")
            try:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        token = result.get("token") or result.get("access_token")
                        if token:
                            print(f"[SUCCESS] Token Issued! (Expires: {result.get('expires_dt')})")
                        else:
                            code = result.get("return_code") or result.get("error")
                            msg = result.get("return_msg") or result.get("error_description")
                            print(f"[FAILED] {msg} (Code: {code})")
                    else:
                        print(f"[ERROR] HTTP {response.status}: {await response.text()}")
            except Exception as e:
                print(f"[ERROR] Exception: {e}")

if __name__ == "__main__":
    # Corrected keys from user
    app_key = "YOUR_APP_KEY"
    secret_key = "YOUR_SECRET_KEY"
    
    asyncio.run(test_key(app_key, secret_key))
