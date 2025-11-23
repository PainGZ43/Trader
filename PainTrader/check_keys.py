import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.config import config
from core.secure_storage import secure_storage

def check_keys():
    print("=== Checking API Keys ===")
    
    keys = ["KIWOOM_APP_KEY", "KIWOOM_SECRET_KEY", "ACCOUNT_NO"]
    
    for key in keys:
        # Check Config (.env)
        config_val = config.get(key)
        config_status = "FOUND" if config_val else "MISSING"
        if config_val:
            masked = config_val[:4] + "*" * (len(config_val)-4) if len(config_val) > 4 else "****"
        else:
            masked = "N/A"
            
        print(f"Config [{key}]: {config_status} ({masked})")
        
        # Check Secure Storage (Keyring)
        secure_val = secure_storage.get(key)
        secure_status = "FOUND" if secure_val else "MISSING"
        
        print(f"SecureStorage [{key}]: {secure_status}")

    print(f"\nMOCK_MODE in Config: {config.get('MOCK_MODE')}")

if __name__ == "__main__":
    check_keys()
