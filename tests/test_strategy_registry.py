import pytest
import sys
import os
sys.path.append(os.getcwd())

from strategy.registry import StrategyRegistry
from strategy.strategies import VolatilityBreakoutStrategy, RSIStrategy

def test_strategy_discovery():
    StrategyRegistry.initialize()
    strategies = StrategyRegistry.get_all_strategies()
    
    assert "VolatilityBreakoutStrategy" in strategies
    assert "RSIStrategy" in strategies
    assert "MovingAverageCrossoverStrategy" in strategies
    assert "BollingerBandStrategy" in strategies
    assert "MACDStrategy" in strategies
    assert "DualThrustStrategy" in strategies
    assert "RSI2Strategy" in strategies
    assert "EnvelopeStrategy" in strategies

def test_strategy_schema():
    StrategyRegistry.initialize()
    
    # Test VolatilityBreakoutStrategy Schema
    vb_schema = StrategyRegistry.get_strategy_schema("VolatilityBreakoutStrategy")
    assert "k" in vb_schema
    assert vb_schema["k"]["type"] == "float"
    assert vb_schema["k"]["default"] == 0.5
    
    # Test RSIStrategy Schema
    rsi_schema = StrategyRegistry.get_strategy_schema("RSIStrategy")
    assert "period" in rsi_schema
    assert rsi_schema["period"]["type"] == "int"
    assert rsi_schema["period"]["default"] == 14

def test_strategy_description():
    StrategyRegistry.initialize()
    desc = StrategyRegistry.get_strategy_description("VolatilityBreakoutStrategy")
    assert "Larry Williams" in desc
