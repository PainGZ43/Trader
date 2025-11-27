import pandas as pd
import talib
from typing import Dict, Any, Optional
from strategy.base_strategy import BaseStrategy, Signal
from datetime import datetime

class VolatilityBreakoutStrategy(BaseStrategy):
    """
    Larry Williams' Volatility Breakout Strategy.
    Buy if Price > Open + (Range * k)
    """
    def __init__(self, strategy_id: str, symbol: str):
        super().__init__(strategy_id, symbol)
        self.k = 0.5 # Default k

    def initialize(self, config: Dict[str, Any]):
        super().initialize(config)
        self.k = config.get("k", 0.5)

    def calculate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        # Calculate Range (Prev High - Prev Low)
        df['range'] = df['high'].shift(1) - df['low'].shift(1)
        df['target'] = df['open'] + (df['range'] * self.k)
        
        # Signal: Close > Target
        df['signal'] = 0
        # Buy Signal
        df.loc[df['high'] > df['target'], 'signal'] = 1 
        # Sell Signal (End of Day or Stop Loss - Simplified here to just entry)
        # In real VB, we sell at opening next day or close of today.
        
        return df

    async def on_realtime_data(self, data: Dict[str, Any]) -> Optional[Signal]:
        # Real-time implementation requires tracking daily open and range
        # Simplified for now
        current_price = float(data.get('price', 0))
        # Logic to check target price...
        return None

class MovingAverageCrossoverStrategy(BaseStrategy):
    """
    Golden Cross / Death Cross Strategy.
    """
    def __init__(self, strategy_id: str, symbol: str):
        super().__init__(strategy_id, symbol)
        self.short_window = 5
        self.long_window = 20

    def initialize(self, config: Dict[str, Any]):
        super().initialize(config)
        self.short_window = config.get("short_window", 5)
        self.long_window = config.get("long_window", 20)

    def calculate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['ma_short'] = talib.SMA(df['close'], timeperiod=self.short_window)
        df['ma_long'] = talib.SMA(df['close'], timeperiod=self.long_window)
        
        df['signal'] = 0
        # Golden Cross (Short crosses above Long)
        df.loc[(df['ma_short'] > df['ma_long']) & (df['ma_short'].shift(1) <= df['ma_long'].shift(1)), 'signal'] = 1
        # Death Cross (Short crosses below Long)
        df.loc[(df['ma_short'] < df['ma_long']) & (df['ma_short'].shift(1) >= df['ma_long'].shift(1)), 'signal'] = -1
        
        return df

    async def on_realtime_data(self, data: Dict[str, Any]) -> Optional[Signal]:
        # Need historical buffer to calculate MA
        return None

class RSIStrategy(BaseStrategy):
    """
    RSI Mean Reversion Strategy.
    Buy if RSI < 30, Sell if RSI > 70.
    """
    def __init__(self, strategy_id: str, symbol: str):
        super().__init__(strategy_id, symbol)
        self.period = 14
        self.buy_threshold = 30
        self.sell_threshold = 70

    def initialize(self, config: Dict[str, Any]):
        super().initialize(config)
        self.period = config.get("period", 14)
        self.buy_threshold = config.get("buy_threshold", 30)
        self.sell_threshold = config.get("sell_threshold", 70)

    def calculate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['rsi'] = talib.RSI(df['close'], timeperiod=self.period)
        
        df['signal'] = 0
        df.loc[df['rsi'] < self.buy_threshold, 'signal'] = 1
        df.loc[df['rsi'] > self.sell_threshold, 'signal'] = -1
        
        return df

    async def on_realtime_data(self, data: Dict[str, Any]) -> Optional[Signal]:
        return None

class BollingerBandStrategy(BaseStrategy):
    """
    Bollinger Band Strategy.
    Buy if Price < Lower Band, Sell if Price > Upper Band.
    """
    def __init__(self, strategy_id: str, symbol: str):
        super().__init__(strategy_id, symbol)
        self.period = 20
        self.std_dev = 2

    def initialize(self, config: Dict[str, Any]):
        super().initialize(config)
        self.period = config.get("period", 20)
        self.std_dev = config.get("std_dev", 2)

    def calculate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        upper, middle, lower = talib.BBANDS(df['close'], timeperiod=self.period, nbdevup=self.std_dev, nbdevdn=self.std_dev)
        df['bb_upper'] = upper
        df['bb_lower'] = lower
        
        df['signal'] = 0
        df.loc[df['close'] < df['bb_lower'], 'signal'] = 1
        df.loc[df['close'] > df['bb_upper'], 'signal'] = -1
        
        return df

    async def on_realtime_data(self, data: Dict[str, Any]) -> Optional[Signal]:
        return None
