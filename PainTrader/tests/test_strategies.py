import pytest
import pandas as pd
import numpy as np
from strategy.factory import StrategyFactory
from strategy.strategies import (
    VolatilityBreakoutStrategy,
    MovingAverageCrossoverStrategy,
    RSIStrategy,
    BollingerBandStrategy
)

@pytest.fixture
def sample_data():
    """Create sample OHLCV data."""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    df = pd.DataFrame({
        'open': np.random.randn(100).cumsum() + 100,
        'high': np.random.randn(100).cumsum() + 105,
        'low': np.random.randn(100).cumsum() + 95,
        'close': np.random.randn(100).cumsum() + 100,
        'volume': np.random.randint(100, 1000, 100)
    }, index=dates)
    # Ensure High >= Low, etc.
    df['high'] = df[['open', 'close', 'high']].max(axis=1)
    df['low'] = df[['open', 'close', 'low']].min(axis=1)
    return df

def test_strategy_factory():
    """Test Strategy Factory creation."""
    strategy = StrategyFactory.create_strategy("RSI", "test_rsi", "005930")
    assert isinstance(strategy, RSIStrategy)
    assert strategy.strategy_id == "test_rsi"
    assert strategy.symbol == "005930"

    with pytest.raises(ValueError):
        StrategyFactory.create_strategy("Unknown", "test", "005930")

def test_rsi_strategy(sample_data):
    """Test RSI Strategy signal generation."""
    strategy = RSIStrategy("rsi_1", "005930")
    strategy.initialize({"period": 14, "buy_threshold": 30, "sell_threshold": 70})
    
    # Manipulate data to force RSI signals
    # Create a sharp drop to trigger RSI < 30
    sample_data.iloc[20:30, 3] = sample_data.iloc[20:30, 3] * 0.8 
    
    result = strategy.calculate_signals(sample_data)
    assert 'rsi' in result.columns
    assert 'signal' in result.columns
    # Check if any signal is generated (might not be guaranteed with random data, but likely)
    # We can check logic: if rsi < 30, signal should be 1
    
    buy_signals = result[result['rsi'] < 30]
    if not buy_signals.empty:
        assert (buy_signals['signal'] == 1).all()

def test_ma_crossover_strategy(sample_data):
    """Test MA Crossover Strategy."""
    strategy = MovingAverageCrossoverStrategy("ma_1", "005930")
    strategy.initialize({"short_window": 5, "long_window": 20})
    
    result = strategy.calculate_signals(sample_data)
    assert 'ma_short' in result.columns
    assert 'ma_long' in result.columns
    assert 'signal' in result.columns

def test_volatility_breakout_strategy(sample_data):
    """Test Volatility Breakout Strategy."""
    strategy = VolatilityBreakoutStrategy("vb_1", "005930")
    strategy.initialize({"k": 0.5})
    
    result = strategy.calculate_signals(sample_data)
    assert 'range' in result.columns
    assert 'target' in result.columns
    assert 'signal' in result.columns
    
    # Check logic: if high > target, signal should be 1
    buy_signals = result[result['high'] > result['target']]
    if not buy_signals.empty:
        assert (buy_signals['signal'] == 1).all()

def test_bollinger_band_strategy(sample_data):
    """Test Bollinger Band Strategy."""
    strategy = BollingerBandStrategy("bb_1", "005930")
    strategy.initialize({"period": 20, "std_dev": 2})
    
    result = strategy.calculate_signals(sample_data)
    assert 'bb_upper' in result.columns
    assert 'bb_lower' in result.columns
    assert 'signal' in result.columns
    
    # Check logic: close < lower -> buy (1)
    buy_signals = result[result['close'] < result['bb_lower']]
    if not buy_signals.empty:
        assert (buy_signals['signal'] == 1).all()
