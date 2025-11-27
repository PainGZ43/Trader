import pandas as pd
import numpy as np
from strategy.market_regime import MarketRegimeDetector, MarketRegime

def test_market_regime():
    print("--- Testing Market Regime Detector ---")
    detector = MarketRegimeDetector()
    
    # Create Mock Data (100 days)
    dates = pd.date_range(start="2023-01-01", periods=100)
    
    # 1. Bull Market Scenario
    print("\n[Scenario 1: Bull Market]")
    close = np.linspace(100, 200, 100) # Steady rise
    high = close + 2
    low = close - 2
    df_bull = pd.DataFrame({
        'open': close, 'high': high, 'low': low, 'close': close, 'volume': 1000
    }, index=dates)
    
    result = detector.detect(df_bull)
    print(f"Regime: {result['regime']}")
    print(f"Details: {result['details']}")
    print(f"Indicators: {result['indicators']}")
    
    # 2. Bear Market Scenario
    print("\n[Scenario 2: Bear Market]")
    close = np.linspace(200, 100, 100) # Steady fall
    high = close + 2
    low = close - 2
    df_bear = pd.DataFrame({
        'open': close, 'high': high, 'low': low, 'close': close, 'volume': 1000
    }, index=dates)
    
    result = detector.detect(df_bear)
    print(f"Regime: {result['regime']}")
    
    # 3. Volatile Scenario
    print("\n[Scenario 3: Volatile Market]")
    close = np.full(100, 100.0)
    # Add noise
    noise = np.random.normal(0, 5, 100) # High variance
    close = close + noise
    high = close + 5
    low = close - 5
    df_vol = pd.DataFrame({
        'open': close, 'high': high, 'low': low, 'close': close, 'volume': 1000
    }, index=dates)
    
    result = detector.detect(df_vol)
    print(f"Regime: {result['regime']}")
    print(f"ATR Ratio: {result['indicators'].get('atr_ratio')}")

if __name__ == "__main__":
    test_market_regime()
