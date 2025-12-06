import sys
import os
import asyncio

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def verify_system():
    print("Starting System Verification...")
    
    try:
        print("1. Verifying KeyManager...")
        from data.key_manager import key_manager
        
        required_methods = [
            "add_key", "delete_key", "update_key_owner", 
            "set_active_key", "get_active_key", "verify_key_by_uuid",
            "is_auto_login_enabled", "set_auto_login_enabled",
            "get_keys", "check_expiration", "get_expiry_alert_days", "set_expiry_alert_days"
        ]
        
        for method in required_methods:
            if not hasattr(key_manager, method):
                print(f"[FAIL] KeyManager missing method: {method}")
                return
            else:
                print(f"  - Found {method}")
                
        print("[PASS] KeyManager integrity check passed.")
        
    except Exception as e:
        print(f"[FAIL] KeyManager import/init failed: {e}")
        return

    try:
        print("2. Verifying KiwoomRestClient...")
        from data.kiwoom_rest_client import kiwoom_client
        print(f"  - Initialized. Base URL: {kiwoom_client.base_url}")
        print("[PASS] KiwoomRestClient integrity check passed.")
    except Exception as e:
        print(f"[FAIL] KiwoomRestClient import/init failed: {e}")
        return

    try:
        print("3. Verifying WebSocketClient...")
        from data.websocket_client import ws_client
        print(f"  - Initialized. Mock Mode: {ws_client.mock_mode}")
        print("[PASS] WebSocketClient integrity check passed.")
    except Exception as e:
        print(f"[FAIL] WebSocketClient import/init failed: {e}")
        return
        
    print("\n[SUCCESS] All checks passed. System is ready.")

if __name__ == "__main__":
    asyncio.run(verify_system())
