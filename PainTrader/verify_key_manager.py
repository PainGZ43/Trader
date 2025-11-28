import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.key_manager import key_manager

async def test_key_manager():
    print("=== Testing KeyManager Backend ===")
    
    # 1. Add Mock Key (Corrected Mock Key)
    print("\n[1] Adding Mock Key...")
    owner = "Test Mock"
    key_type = "MOCK"
    account = "YOUR_MOCK_ACCOUNT"
    app_key = "YOUR_MOCK_APP_KEY"
    secret = "YOUR_MOCK_SECRET_KEY"
    expiry = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
    
    # Verify first (mocking the verify call or using real one)
    # We use the real verify_key method which calls the API
    print("Verifying key with API...")
    is_valid = await key_manager.verify_key(app_key, secret, True)
    print(f"Key Valid: {is_valid}")
    
    if is_valid:
        # Check duplicate before adding to avoid error log in test
        if not await key_manager.check_duplicate(app_key):
            await key_manager.add_key(owner, key_type, account, app_key, secret, expiry)
            print("Key added.")
        else:
            print("Key already exists (Skipping add).")
    
    # 2. Add Real Key (Real Account 2)
    print("\n[2] Adding Real Key...")
    owner_real = "Test Real"
    type_real = "REAL"
    acc_real = "YOUR_REAL_ACCOUNT"
    app_real = "YOUR_REAL_APP_KEY"
    sec_real = "YOUR_REAL_SECRET_KEY"
    
    print("Verifying real key with API...")
    is_valid_real = await key_manager.verify_key(app_real, sec_real, False)
    print(f"Real Key Valid: {is_valid_real}")
    
    if is_valid_real:
        if not await key_manager.check_duplicate(app_real):
            await key_manager.add_key(owner_real, type_real, acc_real, app_real, sec_real, expiry)
            print("Real Key added.")
        else:
            print("Real Key already exists (Skipping add).")

    # 3. List Keys (Checking Masking)
    print("\n[3] Listing Keys (Checking Masking)...")
    keys = key_manager.get_keys()
    for k in keys:
        print(f"- {k['owner']} ({k['type']}): {k['masked_account_no']} [Active: {k['is_active']}]")
        # Verify masking format (last 4 visible)
        acc = k['masked_account_no']
        if len(acc) > 4 and not acc.startswith("*"):
             print(f"  WARNING: Masking might be incorrect: {acc}")
        elif len(acc) > 4 and acc[-4:].isdigit() and "*" in acc[:-4]:
             print(f"  Masking OK: {acc}")

    # 4. Verifying & Updating Expiry & Cache
    print("\n[4] Verifying & Updating Expiry & Cache...")
    # Pick the Real key to test expiry update (mock might be static)
    real_key = next((k for k in keys if k['type'] == 'REAL'), None)
    if real_key:
        print(f"Verifying Real Key: {real_key['owner']} (Current Expiry: {real_key['expiry_date']})")
        # We assume verify_key_by_uuid will update it if valid
        is_valid = await key_manager.verify_key_by_uuid(real_key['uuid'])
        print(f"Valid: {is_valid}")
        
        # Reload to check if expiry changed and is_valid is set
        updated_keys = key_manager.get_keys()
        updated_real = next((k for k in updated_keys if k['uuid'] == real_key['uuid']), None)
        print(f"Updated Expiry: {updated_real['expiry_date']}")
        print(f"Cached Validity: {updated_real.get('is_valid')}")
        
        if updated_real.get('is_valid') is True:
            print("Validation Cache: OK")
        else:
            print("Validation Cache: FAILED")
    else:
        print("No Real key found to verify.")

    # 6. Checking Expiration (Active Only)
    print("\n[6] Checking Expiration (Active Only)...")
    warning = key_manager.check_active_key_expiration()
    if warning:
        print(f"Active Key Warning: {warning}")
    else:
        print("Active Key Warning: None (Valid)")

    # 7. Testing Global Settings
    print("\n[7] Testing Global Settings...")
    # Default values
    print(f"Default Alert Days: {key_manager.get_expiry_alert_days()}")
    print(f"Default Auto Login: {key_manager.is_auto_login_enabled()}")
    
    # Update values
    key_manager.set_expiry_alert_days(14)
    key_manager.set_auto_login_enabled(True)
    
    print(f"Updated Alert Days: {key_manager.get_expiry_alert_days()}")
    print(f"Updated Auto Login: {key_manager.is_auto_login_enabled()}")
    
    # Verify persistence (reload metadata)
    key_manager.metadata = key_manager._load_metadata()
    print(f"Persisted Alert Days: {key_manager.get_expiry_alert_days()}")
    print(f"Persisted Auto Login: {key_manager.is_auto_login_enabled()}")

    # 8. Test Expiry Format Parsing (Internal Logic Check)
    print("\n[8] Testing Expiry Parsing Logic...")
    # We can't easily unit test private methods without reflection or just trusting the integration test.
    # But we can check if the Real Key expiry is formatted correctly.
    if real_key:
        updated_keys = key_manager.get_keys()
        u_real = next((k for k in updated_keys if k['uuid'] == real_key['uuid']), None)
        print(f"Real Key Expiry Format Check: {u_real['expiry_date']}")
        if len(u_real['expiry_date']) == 10 and u_real['expiry_date'][4] == '-':
            print("Format OK (YYYY-MM-DD)")
        else:
            print(f"Format WARNING: {u_real['expiry_date']}")

    print("\n=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(test_key_manager())
