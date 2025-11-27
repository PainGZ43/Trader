import asyncio
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from execution.notification import NotificationManager
from core.config import config

async def verify_real_notifications():
    print("--- Starting Real Notification Verification ---")
    
    # 1. Initialize Manager
    manager = NotificationManager()
    
    if not manager.enabled:
        print("[ERROR] NotificationManager is disabled. Check .env for KAKAO_ACCESS_TOKEN.")
        return

    print(f"[INFO] Token found: {manager.kakao_token[:10]}...")
    
    await manager.start()
    
    try:
        # 2. Send Info Message (Buy Execution Simulation)
        print("[1/3] Sending Info Message (Buy Execution)...")
        buy_msg = (
            "🚀 [매수 체결] 삼성전자 (005930)\n"
            "체결가: 72,500원\n"
            "수량: 10주\n"
            "총액: 725,000원\n"
            "전략: 변동성 돌파"
        )
        await manager.send_message(buy_msg, level="INFO")
        await asyncio.sleep(1)
        
        # 3. Send Error Message (Order Failure Simulation)
        print("[2/3] Sending Error Message (Order Failure)...")
        error_msg = (
            "⚠️ [주문 실패] SK하이닉스 (000660)\n"
            "주문: 매수 5주 @ 시장가\n"
            "사유: 예수금 부족 (필요: 650,000원 / 보유: 120,500원)"
        )
        await manager.send_message(error_msg, level="ERROR")
        await asyncio.sleep(1)
        
        # 4. Send Daily Report (Realistic PnL)
        print("[3/3] Sending Daily Report...")
        summary = {
            "balance": {
                "total_asset": 15420500,
                "daily_pnl": 320500
            },
            "positions": {
                "005930": {"name": "삼성전자", "qty": 10, "pnl": 15000, "yield": 2.1},
                "035420": {"name": "NAVER", "qty": 5, "pnl": -5000, "yield": -0.5},
                "000660": {"name": "SK하이닉스", "qty": 12, "pnl": 45000, "yield": 3.4}
            }
        }
        await manager.send_daily_report(summary)
        await asyncio.sleep(1)
        
        print("--- Verification Completed. Check your KakaoTalk! ---")
        
        # Wait for all messages to be sent
        print("[INFO] Waiting for remaining messages to be sent...")
        await manager.wait_all_sent()
        
    except Exception as e:
        print(f"[ERROR] Verification Failed: {e}")
    finally:
        await manager.stop()

if __name__ == "__main__":
    # Fix for Windows Console Encoding
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    asyncio.run(verify_real_notifications())
