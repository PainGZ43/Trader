import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.secure_storage import secure_storage

def check_stored_keys():
    print("=== Checking Stored Keys ===")
    app_key = secure_storage.get("KIWOOM_APP_KEY")
    secret_key = secure_storage.get("KIWOOM_SECRET_KEY")
    
    print(f"App Key: {app_key}")
    print(f"Secret : {secret_key}")

if __name__ == "__main__":
    check_stored_keys()
