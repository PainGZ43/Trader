import time
import pandas as pd
import numpy as np
import sys
import os

sys.path.append(os.getcwd())
from strategy.backtester import EventDrivenBacktester
from strategy.strategies import VolatilityBreakoutStrategy

def benchmark():
    # Simulate 4 years of daily data (approx 1000 days)
    dates = pd.date_range(start="2020-01-01", periods=1000, freq="D")
    df = pd.DataFrame({
        "open": np.random.rand(1000) * 100 + 10000,
        "high": np.random.rand(1000) * 100 + 10100,
        "low": np.random.rand(1000) * 100 + 9900,
        "close": np.random.rand(1000) * 100 + 10000,
        "volume": np.random.randint(1000, 100000, 1000)
    }, index=dates)
    
    strategy = VolatilityBreakoutStrategy("Bench", "005930")
    strategy.initialize({})
    
    backtester = EventDrivenBacktester()
    backtester.configure({})
    
    start_time = time.time()
    strategy.calculate_signals(df)
    backtester.run(strategy, df)
    end_time = time.time()
    
    duration = end_time - start_time
    print(f"Time per stock (1000 days): {duration:.4f} seconds")
    
    # Estimate for 2500 stocks
    total_serial = duration * 2500
    print(f"Estimated serial time for 2500 stocks: {total_serial:.2f} seconds")
    
    # Estimate parallel (assuming 8 cores, 70% efficiency)
    parallel = total_serial / 8 / 0.7
    print(f"Estimated parallel time (8 cores): {parallel:.2f} seconds")

if __name__ == "__main__":
    benchmark()
