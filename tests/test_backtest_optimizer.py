import pytest
import pandas as pd
import numpy as np
from strategy.backtester import EventDrivenBacktester
from strategy.optimizer import StrategyOptimizer
from strategy.strategies import VolatilityBreakoutStrategy

@pytest.fixture
def sample_data():
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    # Create a predictable trend for VB strategy
    # Day 1: Open 100, High 110, Low 90, Close 105 (Range 20)
    # Day 2: Open 105, Target = 105 + (20 * 0.5) = 115. High 120 -> Buy. Close 118.
    
    data = []
    price = 100
    for i in range(100):
        open_p = price
        high_p = price + 10
        low_p = price - 5
        close_p = price + 5 # Up trend
        data.append([open_p, high_p, low_p, close_p, 1000])
        price = close_p
        
    df = pd.DataFrame(data, columns=['open', 'high', 'low', 'close', 'volume'], index=dates)
    return df

def test_backtester_run(sample_data):
    backtester = EventDrivenBacktester()
    strategy = VolatilityBreakoutStrategy("test_vb", "005930")
    strategy.initialize({"k": 0.5})
    
    result = backtester.run(strategy, sample_data)
    
    assert result.total_return > 0
    assert len(result.trades) > 0
    assert result.final_capital > backtester.initial_capital

def test_optimizer_grid_search(sample_data):
    optimizer = StrategyOptimizer()
    param_grid = {
        "k": [0.1, 0.5, 0.9]
    }
    
    # VB Strategy works best with lower k in strong uptrend (easier breakout)
    # But too low k might cause false signals.
    # In our synthetic data (steady uptrend), lower k should trigger more trades and profit.
    
    best = optimizer.grid_search(VolatilityBreakoutStrategy, param_grid, sample_data)
    
    assert best['best_params'] is not None
    assert best['best_score'] > 0
    # k=0.1 or 0.5 should be better than 0.9
    assert best['best_params']['k'] in [0.1, 0.5]
