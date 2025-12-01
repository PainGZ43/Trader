import asyncio
import sys
import os
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.logger import get_logger
from core.config import config
from execution.notification import NotificationManager

# Configure logging
sys.stdout.reconfigure(encoding='utf-8')
logger = get_logger("VerifyKakao")
logging.basicConfig(level=logging.INFO)

async def main():
    print("=" * 60)
    print("   VERIFY KAKAO SETUP")
    print("=" * 60)

    # 1. Register App Key
    new_app_key = "YOUR_REST_API_KEY" # Replace with your actual REST API Key
    print(f"\n[Step 1] Registering App Key: {new_app_key}")
    config.save("KAKAO_APP_KEY", new_app_key)
    print(" - App Key Saved to Config.")

    # 2. Check Access Token
    print("\n[Step 2] Checking Access Token...")
    token = config.get("KAKAO_ACCESS_TOKEN")
    if token:
        print(f" - Found existing Access Token: {token[:10]}...")
        
        # 3. Try Sending Message
        print("\n[Step 3] Sending Test Message...")
        noti = NotificationManager()
        # Force enable if it was disabled due to missing token at init (though we have it now)
        noti.enabled = True 
        noti.kakao_token = token
        
        await noti.start()
        await noti.send_message("🚀 [테스트] 카카오톡 알림 발송 테스트입니다.", level="INFO")
        
        # Wait a bit for processing
        await asyncio.sleep(2)
        await noti.stop()
        print(" - Message send attempt completed. Check logs for success/failure.")
    else:
        print(" - No Access Token found in Config.")
        print(" - Please generate an Access Token using the 'Get Token' feature in Settings or provide it.")
        
        # Try using the provided key as Access Token just in case (very unlikely)
        print("\n[Step 3-Alt] Trying provided key as Access Token (Fallback)...")
        noti = NotificationManager()
        noti.enabled = True
        noti.kakao_token = new_app_key
        
        await noti.start()
        await noti.send_message("🚀 [테스트] App Key를 토큰으로 사용한 테스트입니다.", level="INFO")
        await asyncio.sleep(2)
        await noti.stop()

    print("\n" + "=" * 60)
    print("   VERIFICATION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
