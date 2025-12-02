import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from strategy.backtester import EventDrivenBacktester
from strategy.strategies import MovingAverageCrossoverStrategy

def generate_mock_data(days=100):
    dates = [datetime(2023, 1, 1) + timedelta(days=i) for i in range(days)]
    # Generate a sine wave price to ensure crossovers
    x = np.linspace(0, 4 * np.pi, days)
    prices = 100 + 10 * np.sin(x)
    
    data = []
    for i, date in enumerate(dates):
        price = prices[i]
        data.append({
            "timestamp": date,
            "open": price,
            "high": price + 1,
            "low": price - 1,
            "close": price,
            "volume": 10000
        })
    
    df = pd.DataFrame(data)
    df.set_index('timestamp', inplace=True)
    return df

async def main():
    print("=" * 50)
    print("   VERIFYING BACKTEST ENGINE")
    print("=" * 50)
    
    # 1. Setup Data
    df = generate_mock_data(200)
    print(f"[Data] Generated {len(df)} rows of mock data (Sine Wave).")
    
    # 2. Setup Strategy
    strategy = MovingAverageCrossoverStrategy("MA_BACKTEST", "MOCK_SYM")
    strategy.initialize({"short_window": 10, "long_window": 30})
    print("[Strategy] Initialized MovingAverageCrossoverStrategy (10/30).")
    
    # 3. Setup Backtester
    backtester = EventDrivenBacktester()
    backtester.configure({
        "initial_capital": 10_000_000,
        "commission_rate": 0.00015,
        "slippage_rate": 0.0005,
        "latency_ticks": 1
    })
    print("[Backtester] Configured with 10M KRW capital.")
    
    # 4. Run
    result = backtester.run(strategy, df)
    
    # 5. Report
    print("\n[Results]")
    print(f"Total Return: {result.total_return:.2f}%")
    print(f"Final Capital: {result.final_capital:,.0f} KRW")
    print(f"MDD: {result.mdd:.2f}%")
    print(f"Win Rate: {result.win_rate:.2f}%")
    print(f"Total Trades: {len(result.trades)}")
    
    if len(result.trades) > 0:
        print("\n[Sample Trades]")
        for t in result.trades[:3]:
            print(t)
        print("...")
        
    if result.total_return != 0.0:
        print("\nSUCCESS: Backtest produced non-zero return.")
    else:
        print("\nWARNING: Backtest return is 0.0%. Check if strategy generated signals.")

if __name__ == "__main__":
    asyncio.run(main())
