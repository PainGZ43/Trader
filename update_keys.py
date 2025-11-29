import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.secure_storage import secure_storage

def update_keys():
    print("=== Updating API Keys ===")
    
    # Credentials from user image
    app_key = "ZR3BLQaFzm8NqhmpX3j2fr3M8BzqxlDNElbjoN26viE"
    secret_key = "e4h10TwInywHa1FN0Dxupt-Y1lj8EkGukZJ2MohCdVs"
    account_no = "81153579"
    
    try:
        secure_storage.save("KIWOOM_APP_KEY", app_key)
        secure_storage.save("KIWOOM_SECRET_KEY", secret_key)
        secure_storage.save("ACCOUNT_NO", account_no)
        print("Keys updated successfully.")
    except Exception as e:
        print(f"Failed to update keys: {e}")

if __name__ == "__main__":
    update_keys()
