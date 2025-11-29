import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.config import config
from core.secure_storage import secure_storage

def check_keys():
    print("=== Checking API Key Format ===")
    
    # Load raw keys
    app_key = secure_storage.get("KIWOOM_APP_KEY") or config.get("KIWOOM_APP_KEY")
    secret_key = secure_storage.get("KIWOOM_SECRET_KEY") or config.get("KIWOOM_SECRET_KEY")
    
    if not app_key:
        print("ERROR: KIWOOM_APP_KEY is missing.")
    else:
        print(f"App Key: {app_key}")
        
    if not secret_key:
        print("ERROR: KIWOOM_SECRET_KEY is missing.")
    else:
        print(f"Secret Key: {secret_key}")

if __name__ == "__main__":
    check_keys()
