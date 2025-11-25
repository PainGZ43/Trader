import asyncio
import sys
import os
import aiohttp
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.key_manager import key_manager

async def debug_api_response():
    print("=== Debugging API Response for Expiry Date ===")
    
    keys = key_manager.get_keys()
    real_key = next((k for k in keys if k['type'] == 'REAL'), None)
    mock_key = next((k for k in keys if k['type'] == 'MOCK'), None)
    
    target_key = real_key or mock_key
    
    if not target_key:
        print("No Real or Mock key found to test.")
        return

    print(f"Testing with Key: {target_key['owner']} ({target_key['type']})")
    
    # Get credentials
    full_key = key_manager.get_active_key() # This gets active, let's just get specific one manually
    # We need to decrypt, but key_manager has no public decrypt method for arbitrary uuid easily exposed without modifying it.
    # But wait, verify_key_by_uuid does it.
    # Let's just use the active key if available, or just use the one we found if we can get secrets.
    
    # Actually, let's just use the internal probe logic but print the response.
    # I will copy the probe logic here to print raw response.
    
    uuid = target_key['uuid']
    from core.secure_storage import secure_storage
    secure_json = secure_storage.get(f"API_KEY_{uuid}")
    if not secure_json:
        print("Secure storage missing.")
        return
        
    keys_data = json.loads(secure_json)
    app_key = keys_data["app_key"]
    secret_key = keys_data["secret_key"]
    
    url = "https://api.kiwoom.com/oauth2/token" if target_key['type'] == 'REAL' else "https://mockapi.kiwoom.com/oauth2/token"
    
    headers = {"Content-Type": "application/json;charset=UTF-8"}
    data = {
        "grant_type": "client_credentials",
        "appkey": app_key,
        "secretkey": secret_key
    }
    
    print(f"Sending request to: {url}")
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as resp:
            print(f"Status Code: {resp.status}")
            text = await resp.text()
            print(f"Raw Response Body:\n{text}")
            
            if resp.status == 200:
                json_resp = json.loads(text)
                print(f"Parsed expires_dt: {json_resp.get('expires_dt')}")
                print(f"Parsed expires_in: {json_resp.get('expires_in')}")

if __name__ == "__main__":
    asyncio.run(debug_api_response())
