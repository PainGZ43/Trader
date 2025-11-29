import pandas as pd
import talib
import numpy as np
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
        
        return df

    def update_market_data(self, df: pd.DataFrame):
        """
        Calculate target price based on previous day's data.
        """
        if df.empty:
            return
            
        try:
            last_row = df.iloc[-1]
            prev_high = last_row['high']
            prev_low = last_row['low']
            
            # Range = Prev High - Prev Low
            rng = prev_high - prev_low
            
            self.prev_range = rng
            self.logger.info(f"Updated Market Data. Prev Range: {self.prev_range}")
            
        except Exception as e:
            self.logger.error(f"Failed to update market data: {e}")

    async def on_realtime_data(self, data: Dict[str, Any]) -> Optional[Signal]:
        """
        Real-time Logic:
        1. If first tick of day, set Target Price.
        2. If Price > Target, Buy.
        """
        try:
            current_price = float(data.get('price', 0))
            timestamp = datetime.now()
            
            daily_open = float(data.get('open', 0))
            if daily_open == 0:
                return None
                
            if not hasattr(self, 'prev_range'):
                return None
                
            target_price = daily_open + (self.prev_range * self.k)
            
            # Check Signal
            if current_price > target_price:
                # Only buy if we haven't bought yet (Position == 0)
                if self.state.current_position == 0:
                    return Signal(
                        symbol=self.symbol,
                        type='BUY',
                        price=current_price,
                        timestamp=timestamp,
                        reason=f"Price {current_price} > Target {target_price} (Range {self.prev_range}, k {self.k})"
                    )
                    
        except Exception as e:
            self.logger.error(f"Error in on_realtime_data: {e}")
            
        return None

class MovingAverageCrossoverStrategy(BaseStrategy):
    """
    Golden Cross / Death Cross Strategy.
    """
    def __init__(self, strategy_id: str, symbol: str):
        super().__init__(strategy_id, symbol)
        self.short_window = 5
        self.long_window = 20
        self.prices = [] # Buffer for realtime MA

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

    def update_market_data(self, df: pd.DataFrame):
        """
        Fill buffer with historical close prices.
        """
        if not df.empty:
            self.prices = df['close'].tolist()
            # Keep only necessary length
            max_len = self.long_window + 5
            if len(self.prices) > max_len:
                self.prices = self.prices[-max_len:]

    async def on_realtime_data(self, data: Dict[str, Any]) -> Optional[Signal]:
        try:
            current_price = float(data.get('price', 0))
            self.prices.append(current_price)
            
            if len(self.prices) < self.long_window + 1:
                return None
                
            closes = np.array(self.prices, dtype=float)
            
            ma_short = talib.SMA(closes, timeperiod=self.short_window)[-1]
            ma_long = talib.SMA(closes, timeperiod=self.long_window)[-1]
            
            prev_ma_short = talib.SMA(closes[:-1], timeperiod=self.short_window)[-1]
            prev_ma_long = talib.SMA(closes[:-1], timeperiod=self.long_window)[-1]
            
            timestamp = datetime.now()
            
            # Golden Cross
            if ma_short > ma_long and prev_ma_short <= prev_ma_long:
                if self.state.current_position == 0:
                    return Signal(self.symbol, 'BUY', current_price, timestamp, f"Golden Cross ({ma_short:.1f} > {ma_long:.1f})")
            
            # Death Cross
            elif ma_short < ma_long and prev_ma_short >= prev_ma_long:
                if self.state.current_position > 0:
                    return Signal(self.symbol, 'SELL', current_price, timestamp, f"Death Cross ({ma_short:.1f} < {ma_long:.1f})")
                    
        except Exception as e:
            self.logger.error(f"Error in on_realtime_data: {e}")
            
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
        self.prices = [] # Buffer

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

    def update_market_data(self, df: pd.DataFrame):
        if not df.empty:
            self.prices = df['close'].tolist()
            # Keep buffer size: period + lookback
            max_len = self.period * 5 
            if len(self.prices) > max_len:
                self.prices = self.prices[-max_len:]

    async def on_realtime_data(self, data: Dict[str, Any]) -> Optional[Signal]:
        try:
            current_price = float(data.get('price', 0))
            self.prices.append(current_price)
            
            if len(self.prices) < self.period + 1:
                return None
                
            closes = np.array(self.prices, dtype=float)
            rsi = talib.RSI(closes, timeperiod=self.period)[-1]
            
            timestamp = datetime.now()
            
            # Buy Signal
            if rsi < self.buy_threshold:
                if self.state.current_position == 0:
                    return Signal(self.symbol, 'BUY', current_price, timestamp, f"RSI Oversold ({rsi:.1f} < {self.buy_threshold})")
            
            # Sell Signal
            elif rsi > self.sell_threshold:
                if self.state.current_position > 0:
                    return Signal(self.symbol, 'SELL', current_price, timestamp, f"RSI Overbought ({rsi:.1f} > {self.sell_threshold})")
                    
        except Exception as e:
            self.logger.error(f"Error in on_realtime_data: {e}")
            
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
