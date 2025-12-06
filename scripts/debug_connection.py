import sys
import os
import asyncio
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.logger import get_logger
from data.key_manager import key_manager
from data.kiwoom_rest_client import kiwoom_client

async def debug_connection():
    with open("debug_output.txt", "w", encoding="utf-8") as f:
        f.write("--- Starting Debug ---\n")
        
        # 1. Check KeyManager
        f.write("Checking KeyManager...\n")
        try:
            active_key = key_manager.get_active_key()
            if active_key:
                f.write(f"[OK] Active Key Found: {active_key.get('app_key', 'N/A')[:4]}***\n")
            else:
                f.write("[FAIL] No Active Key Found.\n")
                return
        except Exception as e:
            f.write(f"[ERROR] KeyManager Check Failed: {e}\n")
            return

        # 2. Check Token Issue
        f.write("Checking Token Issuance...\n")
        try:
            token = await kiwoom_client.get_token()
            if token:
                f.write(f"[OK] Token Issued: {token[:10]}...\n")
            else:
                f.write("[FAIL] Token Issuance Failed.\n")
                return
        except Exception as e:
            f.write(f"[ERROR] Token Issuance Exception: {e}\n")
            return

        # 3. Check Balance Fetch
        f.write("Checking Balance Fetch...\n")
        try:
            balance = await kiwoom_client.get_account_balance()
            if balance:
                f.write(f"[OK] Balance Response Received: {str(balance)[:100]}...\n")
            else:
                f.write("[FAIL] Balance Fetch Failed (None returned).\n")
        except Exception as e:
            f.write(f"[ERROR] Balance Fetch Exception: {e}\n")

        f.write("--- Debug Complete ---\n")

if __name__ == "__main__":
    # Fix for Windows Event Loop Policy
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(debug_connection())
