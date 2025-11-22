import asyncio
import os
from trading_manager import TradingManager
from ai.sentiment import SentimentAnalyzer
from database import init_db
from logger import logger

# Mock Config for Testing
os.environ["MODE"] = "SIMULATION"

async def test_system_integration():
    print("=== Starting System Integration Test ===")
    
    # 1. Initialize Database
    print("[1] Initializing Database...")
    init_db()
    print("    -> Database Initialized.")

    # 2. Initialize Trading Manager
    print("[2] Initializing Trading Manager...")
    trader = TradingManager()
    print("    -> Trading Manager Initialized.")

    # 3. Test Sentiment Analysis
    print("[3] Testing Sentiment Analysis (Samsung Electronics)...")
    # Note: This might fail if network is blocked, but we want to see it try
    try:
        score = await trader.analyze_market_sentiment("005930")
        print(f"    -> Sentiment Score: {score}")
    except Exception as e:
        print(f"    -> Sentiment Analysis Failed (Expected if no network): {e}")

    # 4. Test Buy Logic (Simulation)
    print("[4] Testing Buy Logic (Simulation)...")
    # Force start for testing
    trader.is_running = True 
    
    initial_balance = trader.balance
    await trader.buy("005930", 10, 70000, "Integration Test")
    
    if trader.balance < initial_balance:
        print(f"    -> Buy Successful. Balance changed: {initial_balance} -> {trader.balance}")
    else:
        print("    -> Buy Failed or Balance not updated.")

    # 5. Test Portfolio Update
    if "005930" in trader.portfolio:
        qty = trader.portfolio["005930"]['qty']
        print(f"    -> Portfolio Updated. Holding: {qty} shares")
    else:
        print("    -> Portfolio Update Failed.")

    print("=== Integration Test Completed ===")

if __name__ == "__main__":
    try:
        asyncio.run(test_system_integration())
    except Exception as e:
        print(f"Test Failed: {e}")
