from typing import Dict, Type
from strategy.base_strategy import BaseStrategy
from strategy.strategies import (
    VolatilityBreakoutStrategy,
    MovingAverageCrossoverStrategy,
    RSIStrategy,
    BollingerBandStrategy
)

class StrategyFactory:
    """
    Factory class to create strategy instances.
    """
    _strategies: Dict[str, Type[BaseStrategy]] = {
        "VolatilityBreakout": VolatilityBreakoutStrategy,
        "MovingAverageCrossover": MovingAverageCrossoverStrategy,
        "RSI": RSIStrategy,
        "BollingerBand": BollingerBandStrategy
    }

    @classmethod
    def create_strategy(cls, strategy_name: str, strategy_id: str, symbol: str) -> BaseStrategy:
        """
        Create a strategy instance by name.
        """
        strategy_cls = cls._strategies.get(strategy_name)
        if not strategy_cls:
            raise ValueError(f"Unknown strategy: {strategy_name}")
        
        return strategy_cls(strategy_id, symbol)

    @classmethod
    def register_strategy(cls, name: str, strategy_cls: Type[BaseStrategy]):
        """
        Register a new strategy class dynamically.
        """
        cls._strategies[name] = strategy_cls
        
    @classmethod
    def get_available_strategies(cls):
        return list(cls._strategies.keys())
