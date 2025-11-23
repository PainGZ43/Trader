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
    account = "81153579"
    app_key = "ZR3BLQaFzm8NqhmPX3j2fr3M8BzqxIDNElbjoN26viE"
    secret = "e4h10TwInywHa1FN0Dxupt-Y1Ij8EkGukZJ2MohCdVs"
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
    acc_real = "55480828"
    app_real = "NUyOeBat-OXdhOlNL2JoanurvJgNJv-60v49yFDKru8"
    sec_real = "rlnQQBXknNjaqqAL3fQs0KGOgeMWi1I9NPl-ykOtTWQ"
    
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

if __name__ == "__main__":
    asyncio.run(test_key_manager())
