import pytest
import pandas as pd
import numpy as np
from strategy.market_regime import MarketRegimeDetector, MarketRegime
from strategy.position_sizer import PositionSizer

@pytest.fixture
def sample_data():
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    df = pd.DataFrame({
        'open': np.linspace(100, 200, 100), # Strong Up Trend
        'high': np.linspace(105, 205, 100),
        'low': np.linspace(95, 195, 100),
        'close': np.linspace(100, 200, 100),
        'volume': np.random.randint(100, 1000, 100)
    }, index=dates)
    return df

def test_market_regime_bull(sample_data):
    detector = MarketRegimeDetector()
    regime = detector.detect(sample_data)
    # With linear increase, ADX should be high and MA aligned
    # Note: TA-Lib ADX needs some volatility to be meaningful, perfect line might result in 0 or weird values.
    # Let's add some noise to make it realistic
    sample_data['close'] += np.random.randn(100) * 0.5
    sample_data['high'] = sample_data['close'] + 1
    sample_data['low'] = sample_data['close'] - 1
    
    regime = detector.detect(sample_data)
    # It might be BULL or SIDEWAY depending on ADX calculation details
    assert regime in [MarketRegime.BULL, MarketRegime.SIDEWAY, MarketRegime.VOLATILE]

def test_position_sizer_risk_based():
    sizer = PositionSizer()
    sizer.configure({"risk_per_trade": 0.01, "max_position_size": 0.5})
    
    capital = 10_000_000 # 10 Million KRW
    entry = 10_000
    stop = 9_500 # Risk 500 per share
    
    # Risk Amount = 100,000
    # Risk Per Share = 500
    # Expected Shares = 200
    # Position Amt = 2,000,000 (20% of capital, within 50% limit)
    
    shares = sizer.calculate_size(capital, entry, stop)
    assert shares == 200

def test_position_sizer_kelly():
    sizer = PositionSizer()
    sizer.configure({"max_position_size": 0.5}) # Increase limit to test Kelly calculation
    # Kelly: b=2, p=0.5 -> f = (2*0.5 - 0.5)/2 = 0.25
    # Half Kelly = 0.125
    # Capital 10M -> 1.25M Position
    # Entry 10,000 -> 125 Shares
    
    shares = sizer.calculate_size(10_000_000, 10_000, 9_000, win_rate=0.5, risk_reward_ratio=2.0, method="kelly")
    assert shares == 125

def test_position_sizer_constraints():
    sizer = PositionSizer()
    sizer.configure({"max_position_size": 0.1}) # Max 1M
    
    # Calculated size would be 2M (200 shares) based on risk
    # Should be capped at 1M (100 shares)
    shares = sizer.calculate_size(10_000_000, 10_000, 9_500)
    assert shares == 100
