import sys
import os
import asyncio

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.key_manager import key_manager
from core.secure_storage import secure_storage

def main():
    print("=" * 50)
    print("   RESETTING ALL KEY INFORMATION")
    print("=" * 50)

    # 1. Get all keys
    keys = key_manager.get_keys()
    print(f"Found {len(keys)} registered keys.")

    # 2. Delete each key from SecureStorage and KeyManager
    for k in keys:
        uuid = k['uuid']
        owner = k['owner']
        print(f"Deleting key for {owner} (UUID: {uuid})...")
        
        # Delete from SecureStorage
        secure_key = f"API_KEY_{uuid}"
        try:
            secure_storage.delete(secure_key)
            print(f" - Removed from SecureStorage: {secure_key}")
        except Exception as e:
            print(f" - Failed to remove from SecureStorage: {e}")

        # Delete from KeyManager (Metadata)
        if key_manager.delete_key(uuid):
            print(f" - Removed from KeyManager")
        else:
            print(f" - Failed to remove from KeyManager")

    # 3. Delete Legacy/Global Keys (if any)
    legacy_keys = ["KIWOOM_APP_KEY", "KIWOOM_SECRET_KEY", "KIWOOM_ACCOUNT"]
    print("\nChecking for legacy keys...")
    for lk in legacy_keys:
        try:
            if secure_storage.get(lk):
                secure_storage.delete(lk)
                print(f" - Removed legacy key: {lk}")
        except Exception:
            pass

    # 4. Verify
    remaining = key_manager.get_keys()
    if not remaining:
        print("\nSUCCESS: All keys have been reset.")
    else:
        print(f"\nWARNING: {len(remaining)} keys still remain.")

if __name__ == "__main__":
    main()
