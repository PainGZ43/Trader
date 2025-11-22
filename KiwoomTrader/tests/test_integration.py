import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading_manager import TradingManager
from config import Config
from database import get_db, TradeLog

async def test_scenario():
    print("Starting Integration Test...")
    Config.MODE = "SIMULATION"
    
    trader = TradingManager()
    await trader.start()
    
    # Test Buy
    print("Testing Buy...")
    await trader.buy("005930", 10, 70000, "Test Buy")
    await asyncio.sleep(1)
    
    # Test Sell
    print("Testing Sell...")
    await trader.sell("005930", 5, 71000, "Test Sell")
    await asyncio.sleep(1)
    
    await trader.stop()
    
    # Verify DB
    db = get_db()
    trades = db.query(TradeLog).all()
    print(f"Trades in DB: {len(trades)}")
    for t in trades:
        print(f" - {t.side} {t.code} {t.qty} @ {t.price} (Profit: {t.profit_pct}%)")
        
    if len(trades) >= 2:
        print("Integration Test Passed!")
    else:
        print("Integration Test Failed: Not enough trades recorded.")

if __name__ == "__main__":
    asyncio.run(test_scenario())
