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

from strategy.market_regime import MarketRegimeDetector

class BaseStrategy(StrategyInterface):
    """
    Base Strategy Implementation with common functionality.
    """
    def __init__(self, strategy_id: str, symbol: str):
        self.logger = get_logger(f"Strategy_{strategy_id}")
        self.strategy_id = strategy_id
        self.symbol = symbol
        self.config = {}
        self.state = StrategyState(strategy_id=strategy_id, symbol=symbol, indicators={}, last_update=datetime.now())
        
        # Components
        self.position_sizer = None 
        self.market_regime_detector = MarketRegimeDetector()

    def initialize(self, config: Dict[str, Any]):
        self.config = config
        self.logger.info(f"Initialized with config: {config}")

    def get_state(self) -> StrategyState:
        return self.state

    def set_state(self, state: StrategyState):
        self.state = state
        self.logger.info(f"State restored: {state}")

    async def on_realtime_data(self, data: Dict[str, Any]) -> Optional[Signal]:
        """
        Default implementation for realtime data processing.
        Subclasses should override or extend this.
        """
        # 1. Update Indicators (Assuming data contains indicators or we calculate them here)
        # In real app, IndicatorEngine might update a shared DF, or we calculate on the fly.
        
        # 2. Check Signals
        # signal = self.check_signal(data)
        
        # 3. Position Sizing
        # if signal:
        #     size = self.position_sizer.calculate_size(...)
        
        return None

    def update_position(self, size: int, price: float):
        """
        Update position state after execution.
        """
        if size > 0: # Buy
            total_cost = (self.state.current_position * self.state.avg_entry_price) + (size * price)
            self.state.current_position += size
            self.state.avg_entry_price = total_cost / self.state.current_position if self.state.current_position != 0 else 0
        elif size < 0: # Sell
            # Calculate Profit
            profit = (price - self.state.avg_entry_price) * abs(size)
            self.state.accumulated_profit += profit
            self.state.current_position += size
            if self.state.current_position == 0:
                self.state.avg_entry_price = 0
        
        self.state.last_update = datetime.now()
