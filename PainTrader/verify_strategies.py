import asyncio
import pandas as pd
import numpy as np
from strategy.built_in_strategies import VolatilityBreakoutStrategy, SimpleMAStrategy, RSIStrategy, BollingerBandStrategy, MACDStrategy

def generate_mock_data(days=50):
    dates = pd.date_range(end=pd.Timestamp.now(), periods=days)
    data = {
        'open': np.random.uniform(100, 200, days),
        'high': np.random.uniform(100, 200, days),
        'low': np.random.uniform(100, 200, days),
        'close': np.random.uniform(100, 200, days),
        'volume': np.random.uniform(1000, 10000, days)
    }
    df = pd.DataFrame(data, index=dates)
    df['high'] = df[['open', 'close', 'high']].max(axis=1)
    df['low'] = df[['open', 'close', 'low']].min(axis=1)
    return df

async def verify_strategies():
    print("=== Verifying Strategies ===")
    df = generate_mock_data(100)
    
    strategies = [
        VolatilityBreakoutStrategy(),
        SimpleMAStrategy(),
        RSIStrategy(),
        BollingerBandStrategy(),
        MACDStrategy()
    ]
    
    for strategy in strategies:
        print(f"\nTesting {strategy.name}...")
        try:
            if isinstance(strategy, VolatilityBreakoutStrategy):
                strategy.calculate_target(df)
                # Simulate realtime data
                await strategy.on_realtime_data({"price": df.iloc[-1]['close']})
            else:
                signal = strategy.calculate_signals(df)
                print(f"Signal: {signal}")
            print("OK")
        except Exception as e:
            print(f"FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(verify_strategies())
