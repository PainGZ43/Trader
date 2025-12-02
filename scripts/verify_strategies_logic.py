import asyncio
import pandas as pd
import numpy as np
from datetime import datetime
from strategy.strategies import VolatilityBreakoutStrategy, MovingAverageCrossoverStrategy, RSIStrategy, BollingerBandStrategy

async def verify_volatility_breakout():
    print("\n[Verifying VolatilityBreakoutStrategy]")
    strategy = VolatilityBreakoutStrategy("VB_TEST", "005930")
    strategy.initialize({"k": 0.5})
    
    # 1. Historical Data (Warm-up)
    # Prev High: 1000, Prev Low: 900 -> Range: 100
    # Target = Open + (100 * 0.5) = Open + 50
    df = pd.DataFrame([
        {"timestamp": datetime(2023, 1, 1), "open": 900, "high": 1000, "low": 900, "close": 950, "volume": 1000}
    ])
    strategy.update_market_data(df)
    
    # 2. Realtime Data
    # Open: 950 -> Target: 950 + 50 = 1000
    # Price: 1010 -> Buy Signal
    data = {"code": "005930", "price": 1010, "open": 950, "volume": 10}
    signal = await strategy.on_realtime_data(data)
    
    if signal and signal.type == "BUY":
        print("SUCCESS: Buy Signal Generated correctly.")
    else:
        print(f"FAILED: Expected Buy Signal, got {signal}")

async def verify_ma_crossover():
    print("\n[Verifying MovingAverageCrossoverStrategy]")
    strategy = MovingAverageCrossoverStrategy("MA_TEST", "005930")
    strategy.initialize({"short_window": 2, "long_window": 5})
    
    # Warm-up with enough data
    # MA2: [10, 10], MA5: [10, 10, 10, 10, 10]
    prices = [10, 10, 10, 10, 10, 10, 10] 
    df = pd.DataFrame({"close": prices})
    strategy.update_market_data(df)
    
    # Current Price: 20 -> MA2 jumps up, MA5 slowly up -> Golden Cross
    data = {"code": "005930", "price": 20}
    signal = await strategy.on_realtime_data(data)
    
    if signal and signal.type == "BUY":
        print("SUCCESS: Golden Cross Signal Generated.")
    else:
        print(f"FAILED: Expected Golden Cross, got {signal}")

async def verify_rsi():
    print("\n[Verifying RSIStrategy]")
    strategy = RSIStrategy("RSI_TEST", "005930")
    strategy.initialize({"period": 2, "buy_threshold": 30, "sell_threshold": 70})
    
    # RSI Calculation needs volatility
    # Drop prices to create Oversold
    prices = [100, 90, 80, 70, 60, 50, 40, 30, 20]
    df = pd.DataFrame({"close": prices})
    strategy.update_market_data(df)
    
    data = {"code": "005930", "price": 10} # Further drop
    signal = await strategy.on_realtime_data(data)
    
    if signal and signal.type == "BUY":
        print("SUCCESS: RSI Buy Signal Generated.")
    else:
        print(f"FAILED: Expected RSI Buy Signal, got {signal}")

async def main():
    await verify_volatility_breakout()
    await verify_ma_crossover()
    await verify_rsi()

if __name__ == "__main__":
    asyncio.run(main())
