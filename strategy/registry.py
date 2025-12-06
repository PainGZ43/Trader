import inspect
import sys
import importlib
from typing import Dict, Type, List, Any
from strategy.base_strategy import BaseStrategy
from strategy import strategies
from core.logger import get_logger

class StrategyRegistry:
    """
    Registry for managing available strategies.
    Automatically discovers strategies inheriting from BaseStrategy.
    """
    _strategies: Dict[str, Type[BaseStrategy]] = {}
    _logger = get_logger("StrategyRegistry")

    @classmethod
    def initialize(cls):
        """
        Discover and register strategies.
        """
        cls._strategies = {}
        cls._discover_strategies_in_module(strategies)
        cls._logger.info(f"Initialized StrategyRegistry. Found {len(cls._strategies)} strategies.")

    @classmethod
    def _discover_strategies_in_module(cls, module):
        """
        Scan a module for BaseStrategy subclasses.
        """
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and issubclass(obj, BaseStrategy) and obj is not BaseStrategy:
                cls.register(obj)

    @classmethod
    def register(cls, strategy_cls: Type[BaseStrategy]):
        """
        Register a strategy class.
        """
        name = strategy_cls.get_name()
        if name in cls._strategies:
            cls._logger.warning(f"Strategy '{name}' already registered. Overwriting.")
        
        cls._strategies[name] = strategy_cls
        cls._logger.debug(f"Registered strategy: {name}")

    @classmethod
    def get_strategy_class(cls, name: str) -> Type[BaseStrategy]:
        """
        Get strategy class by name.
        """
        return cls._strategies.get(name)

    @classmethod
    def get_all_strategies(cls) -> List[str]:
        """
        Get list of all registered strategy names.
        """
        return list(cls._strategies.keys())

    @classmethod
    def get_strategy_schema(cls, name: str) -> Dict[str, Any]:
        """
        Get parameter schema for a strategy.
        """
        strategy_cls = cls.get_strategy_class(name)
        if strategy_cls:
            return strategy_cls.get_parameter_schema()
        return {}

    @classmethod
    def get_strategy_description(cls, name: str) -> str:
        """
        Get description for a strategy.
        """
        strategy_cls = cls.get_strategy_class(name)
        if strategy_cls:
            return strategy_cls.get_description()
        return ""
