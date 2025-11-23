import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.secure_storage import secure_storage

def update_keys():
    print("=== Updating API Keys to Mock Account 1 (Corrected) ===")
    
    # Mock Account 1 (Corrected)
    app_key = "ZR3BLQaFzm8NqhmPX3j2fr3M8BzqxIDNElbjoN26viE"
    secret_key = "e4h10TwInywHa1FN0Dxupt-Y1Ij8EkGukZJ2MohCdVs"
    account_no = "81153579"
    
    secure_storage.save("KIWOOM_APP_KEY", app_key)
    secure_storage.save("KIWOOM_SECRET_KEY", secret_key)
    secure_storage.save("ACCOUNT_NO", account_no)
    
    print("Keys updated successfully.")
    print(f"Account No: {account_no}")

if __name__ == "__main__":
    update_keys()
