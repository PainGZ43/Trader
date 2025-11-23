from abc import ABC, abstractmethod
from core.logger import get_logger

class StrategyInterface(ABC):
    """
    Abstract Base Class for all trading strategies.
    """
    def __init__(self, name, config=None):
        self.name = name
        self.config = config or {}
        self.logger = get_logger(f"Strategy_{name}")

    @abstractmethod
    async def on_realtime_data(self, data):
        """
        Process real-time data (tick/candle).
        :param data: Dictionary containing market data (code, price, volume, etc.)
        :return: Signal (BUY, SELL, NONE) or Order object
        """
        pass

    @abstractmethod
    async def on_candle_close(self, candle):
        """
        Process candle close event.
        :param candle: DataFrame row or dict with OHLCV
        """
        pass

    def set_config(self, config):
        """
        Update strategy configuration.
        """
        self.config.update(config)
        self.logger.info(f"Config updated: {self.config}")
