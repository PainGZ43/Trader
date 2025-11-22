import requests
import json
from config import Config
from logger import logger

class Notifier:
    def __init__(self):
        self.base_url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
        
    def send(self, message):
        """Send 'To Me' message via KakaoTalk"""
        # If no token is set, just log it
        if not Config.KAKAO_ACCESS_TOKEN:
            logger.info(f"[KAKAO SKIP] {message}")
            return True
            
        headers = {
            "Authorization": f"Bearer {Config.KAKAO_ACCESS_TOKEN}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        template = {
            "object_type": "text",
            "text": message,
            "link": {
                "web_url": "https://www.kiwoom.com",
                "mobile_web_url": "https://www.kiwoom.com"
            }
        }
        
        try:
            payload = {"template_object": json.dumps(template)}
            resp = requests.post(self.base_url, headers=headers, data=payload)
            if resp.status_code == 200:
                logger.info("Kakao Notification Sent")
                return True
            else:
                logger.error(f"Kakao Send Failed: {resp.text}")
                # TODO: Implement Refresh Token Logic here if 401
                return False
        except Exception as e:
            logger.error(f"Kakao Error: {e}")
            return False

