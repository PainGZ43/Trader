import pytest
import pandas as pd
import numpy as np
import sys
import os
sys.path.append(os.getcwd())

from optimization.optimizer import Optimizer
from strategy.base_strategy import BaseStrategy, Signal
from typing import Dict, Any, Optional

# Mock Strategy for testing
class MockStrategy(BaseStrategy):
    @classmethod
    def get_parameter_schema(cls):
        return {"param1": {"type": "int"}, "param2": {"type": "float"}}
        
    def __init__(self, strategy_id, symbol):
        super().__init__(strategy_id, symbol)
        self.param1 = 1
        self.param2 = 0.1
        
    def initialize(self, config):
        super().initialize(config)
        self.param1 = config.get("param1", 1)
        self.param2 = config.get("param2", 0.1)
        
    def calculate_signals(self, df):
        df = df.copy()
        df['signal'] = 0
        # Simple logic: Buy if close > open * param2
        df.loc[df['close'] > df['open'] * (1 + self.param2), 'signal'] = 1
        df.loc[df['close'] < df['open'], 'signal'] = -1
        return df

    def update_market_data(self, df):
        pass
        
    async def on_realtime_data(self, data):
        return None

@pytest.fixture
def sample_data():
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    data = {
        'open': np.random.rand(100) * 100,
        'high': np.random.rand(100) * 100,
        'low': np.random.rand(100) * 100,
        'close': np.random.rand(100) * 100,
        'volume': np.random.randint(100, 1000, 100)
    }
    df = pd.DataFrame(data, index=dates)
    return df

def test_grid_generation():
    optimizer = Optimizer()
    ranges = {
        "p1": [1, 2],
        "p2": [0.1, 0.2]
    }
    grid = optimizer.generate_grid(ranges)
    assert len(grid) == 4
    assert {"p1": 1, "p2": 0.1} in grid
    assert {"p1": 2, "p2": 0.2} in grid

def test_optimization_run(sample_data):
    optimizer = Optimizer()
    ranges = {
        "param1": [1, 2],
        "param2": [0.01, 0.05] # Small threshold to ensure some trades
    }
    
    # We need to ensure Backtester can run. 
    # Backtester imports might need mocking if they depend on complex things.
    # But EventDrivenBacktester is relatively pure logic.
    
    results = optimizer.run_optimization(MockStrategy, sample_data, ranges, max_workers=2)
    
    assert not results.empty
    assert "total_return" in results.columns
    assert "param1" in results.columns
    assert len(results) == 4
    
    # Check sorting
    assert results.iloc[0]['total_return'] >= results.iloc[-1]['total_return']
