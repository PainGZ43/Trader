import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.secure_storage import secure_storage

def update_keys():
    print("=== Updating API Keys to Real Account 2 ===")
    
    # Real Account 2 (55480828)
    app_key = "YOUR_APP_KEY"
    secret_key = "YOUR_SECRET_KEY"
    account_no = "YOUR_ACCOUNT_NO"
    
    secure_storage.save("KIWOOM_APP_KEY", app_key)
    secure_storage.save("KIWOOM_SECRET_KEY", secret_key)
    secure_storage.save("ACCOUNT_NO", account_no)
    
    print("Keys updated successfully.")
    print(f"Account No: {account_no}")

if __name__ == "__main__":
    update_keys()
