import requests
import json
import webbrowser
import time
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import asyncio

# Configuration
APP_KEY = "60371040fc940138725aec7013a905c7"
REDIRECT_URI = "http://localhost:5000" # Must match Kakao Developers setting
PORT = 5000

auth_code = None

class OAuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        parsed_path = urlparse(self.path)
        if parsed_path.path == "/":
            query = parse_qs(parsed_path.query)
            if "code" in query:
                auth_code = query["code"][0]
                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"<h1>Authentication Successful!</h1><p>You can close this window and return to the terminal.</p>")
            else:
                self.send_response(400)
                self.wfile.write(b"<h1>Error: No code found</h1>")

def start_server():
    server = HTTPServer(('localhost', PORT), OAuthHandler)
    server.handle_request() # Handle one request then exit

def get_token_auto():
    print(f"1. Starting local server at {REDIRECT_URI}...")
    server_thread = threading.Thread(target=start_server)
    server_thread.start()
    
    print("\n[IMPORTANT CHECKLIST for KOE006 Error]")
    print(f"1. The Redirect URI sent is: '{REDIRECT_URI}'")
    print("2. It must match EXACTLY in Kakao Developers.")
    print("   - No trailing slash (e.g., http://localhost:5000/) -> X")
    print("   - No HTTPS (e.g., https://localhost:5000) -> X (unless configured)")
    print("   - Must be 'http://localhost:5000'")
    print("3. Go to [Kakao Login] -> [Redirect URI] and check for typos.\n")
    
    # 2. Open Browser
    
    # 2. Open Browser
    auth_url = f"https://kauth.kakao.com/oauth/authorize?client_id={APP_KEY}&redirect_uri={REDIRECT_URI}&response_type=code&scope=talk_message"
    print(f"2. Opening browser for login...")
    webbrowser.open(auth_url)
    
    # 3. Wait for code
    print("3. Waiting for authentication...")
    server_thread.join()
    
    if not auth_code:
        print("[ERROR] Failed to get auth code.")
        return

    print(f"\n[SUCCESS] Auth Code received: {auth_code[:10]}...")
    
    # 4. Get Token
    token_url = "https://kauth.kakao.com/oauth/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": APP_KEY,
        "redirect_uri": REDIRECT_URI,
        "code": auth_code
    }
    
    resp = requests.post(token_url, data=data)
    if resp.status_code == 200:
        tokens = resp.json()
        access_token = tokens['access_token']
        refresh_token = tokens['refresh_token']
        
        print(f"[SUCCESS] Tokens retrieved!")
        
        # 5. Save to .env
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
        
        # Read existing
        env_lines = []
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                env_lines = f.readlines()
        
        # Remove old keys
        env_lines = [line for line in env_lines if not line.startswith("KAKAO_ACCESS_TOKEN") and not line.startswith("KAKAO_REFRESH_TOKEN")]
        
        # Append new
        env_lines.append(f"KAKAO_ACCESS_TOKEN={access_token}\n")
        env_lines.append(f"KAKAO_REFRESH_TOKEN={refresh_token}\n")
        
        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(env_lines)
            
        print("[INFO] Tokens saved to .env file.")
        
        # 6. Send Notification
        print("6. Sending confirmation message...")
        # Need to set env var for current process to use it immediately
        os.environ["KAKAO_ACCESS_TOKEN"] = access_token
        os.environ["KAKAO_REFRESH_TOKEN"] = refresh_token
        
        # Import NotificationManager (requires path setup)
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from execution.notification import NotificationManager
        from core.config import config
        
        # Force reload config to pick up env vars
        config._initialize()
        
        async def send_test():
            nm = NotificationManager()
            await nm.start()
            await nm.send_message("✅ [시스템] 카카오톡 API 키 등록 및 인증이 완료되었습니다!")
            await asyncio.sleep(1) # Wait for send
            await nm.stop()
            
        asyncio.run(send_test())
        print("[SUCCESS] Confirmation message sent!")
        
    else:
        print(f"\n[ERROR] Failed to get tokens: {resp.text}")

if __name__ == "__main__":
    get_token_auto()
