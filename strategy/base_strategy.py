from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional, List
import pandas as pd
from core.logger import get_logger

@dataclass
class Signal:
    """
    Trading Signal
    """
    symbol: str
    type: str  # 'BUY', 'SELL', 'EXIT'
    price: float
    timestamp: datetime
    reason: str
    score: float = 0.0

@dataclass
class StrategyState:
    """
    Persistent State of a Strategy
    """
    strategy_id: str
    symbol: str
    current_position: int = 0
    avg_entry_price: float = 0.0
    accumulated_profit: float = 0.0
    indicators: Dict[str, float] = None
    last_update: datetime = None

class StrategyInterface(ABC):
    """
    Abstract Base Class for all Trading Strategies.
    """
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]):
        """
        Initialize strategy with configuration.
        """
        pass

    @abstractmethod
    async def on_realtime_data(self, data: Dict[str, Any]) -> Optional[Signal]:
        """
        Process real-time data (tick/bar) and return Signal if any.
        """
        pass

    @abstractmethod
    def calculate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate signals on historical data (for backtesting).
        Returns DataFrame with 'signal' column.
        """
        pass

    @abstractmethod
    def get_state(self) -> StrategyState:
        """
        Return current state for persistence.
        """
        pass

    @abstractmethod
    def set_state(self, state: StrategyState):
        """
        Restore state from persistence.
        """
        pass

    @abstractmethod
    def update_market_data(self, df: pd.DataFrame):
        """
        Update strategy with historical market data (Warm-up).
        """
    @abstractmethod
    def pause(self):
        """Pause strategy execution."""
        pass

    @abstractmethod
    def resume(self):
        """Resume strategy execution."""
        pass

    @property
    @abstractmethod
    def is_active(self) -> bool:
        """Check if strategy is active."""
        pass

from strategy.market_regime import MarketRegimeDetector

class BaseStrategy(StrategyInterface):
    """
    Base Strategy Implementation with common functionality.
    """
    @classmethod
    @abstractmethod
    def get_parameter_schema(cls) -> Dict[str, Dict[str, Any]]:
        """
        Define tunable parameters for the strategy.
        Returns a dictionary where key is parameter name and value is metadata.
        Example:
        {
            "rsi_period": {"type": "int", "min": 5, "max": 30, "default": 14, "desc": "RSI Period"},
            "stop_loss_pct": {"type": "float", "min": 0.5, "max": 5.0, "default": 2.0, "desc": "Stop Loss %"}
        }
        """
        return {}

    @classmethod
    def get_name(cls) -> str:
        """Return strategy name."""
        return cls.__name__

    @classmethod
    def get_description(cls) -> str:
        """Return strategy description."""
        return cls.__doc__.strip() if cls.__doc__ else "No description available."

    def __init__(self, strategy_id: str, symbol: str):
        self.logger = get_logger(f"Strategy_{strategy_id}")
        self.strategy_id = strategy_id
        self.symbol = symbol
        self.config = {}
        self.state = StrategyState(strategy_id=strategy_id, symbol=symbol, indicators={}, last_update=datetime.now())
        self._is_active = True
        
        # Components
        self.position_sizer = None 
        self.market_regime_detector = MarketRegimeDetector()

    def initialize(self, config: Dict[str, Any]):
        self.config = config
        self.logger.info(f"Initialized with config: {config}")

    def pause(self):
        self._is_active = False
        self.logger.info("Strategy Paused")

    def resume(self):
        self._is_active = True
        self.logger.info("Strategy Resumed")

    @property
    def is_active(self) -> bool:
        return self._is_active

    def get_state(self) -> StrategyState:
        return self.state

    def set_state(self, state: StrategyState):
        self.state = state
        self.logger.info(f"State restored: {state}")

    def update_market_data(self, df: pd.DataFrame):
        """
        Default implementation: Do nothing.
        Subclasses can override to warm up indicators.
        """
        pass

    async def on_realtime_data(self, data: Dict[str, Any]) -> Optional[Signal]:
        """
        Default implementation for realtime data processing.
        Subclasses should override or extend this.
        """
        if not self.is_active:
            return None

        # 1. Update Indicators (Assuming data contains indicators or we calculate them here)
        # In real app, IndicatorEngine might update a shared DF, or we calculate on the fly.
        
        # 2. Check Signals
        # signal = self.check_signal(data)
        
        # 3. Position Sizing
        # if signal:
        #     size = self.position_sizer.calculate_size(...)
        
        return None

    def update_position(self, price: float, qty: int, order_type: str):
        """
        Update position state after execution.
        """
        if order_type == "BUY":
            total_cost = (self.state.current_position * self.state.avg_entry_price) + (qty * price)
            self.state.current_position += qty
            self.state.avg_entry_price = total_cost / self.state.current_position if self.state.current_position != 0 else 0
        elif order_type == "SELL":
            # Calculate Profit
            profit = (price - self.state.avg_entry_price) * qty
            self.state.accumulated_profit += profit
            self.state.current_position -= qty
            if self.state.current_position == 0:
                self.state.avg_entry_price = 0
        
        self.state.last_update = datetime.now()
