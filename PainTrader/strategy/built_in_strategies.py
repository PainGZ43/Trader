from strategy.strategy_interface import StrategyInterface
from data.indicator_engine import indicator_engine
import pandas as pd

class VolatilityBreakoutStrategy(StrategyInterface):
    """
    Volatility Breakout Strategy (Larry Williams).
    Buy if Price > Open + (Range * k)
    """
    def __init__(self, name="VolBreakout", config=None):
        super().__init__(name, config)
        self.k = self.config.get("k", 0.5)
        self.target_price = None
        self.symbol = None

    def calculate_target(self, df):
        """
        Calculate target price based on previous day's range.
        Target = Today's Open + (Yesterday's High - Yesterday's Low) * k
        """
        if len(df) < 2:
            return
        
        # Assuming df is daily data sorted by date
        yesterday = df.iloc[-2]
        today_open = df.iloc[-1]['open']
        
        range_val = yesterday['high'] - yesterday['low']
        self.target_price = today_open + range_val * self.k
        self.logger.info(f"Target Price Calculated: {self.target_price} (Range: {range_val}, k: {self.k})")

    async def on_realtime_data(self, data):
        """
        Check for breakout.
        """
        if self.target_price is None:
            return None

        current_price = data.get("price")
        if current_price is None:
            return None
            
        if current_price >= self.target_price:
            self.logger.info(f"Breakout Detected! Price: {current_price} >= Target: {self.target_price}")
            return {"signal": "BUY", "price": current_price, "strategy": self.name}
        
        return None

    async def on_candle_close(self, candle):
        pass

class SimpleMAStrategy(StrategyInterface):
    """
    Simple Moving Average Crossover Strategy.
    """
    def __init__(self, name="SimpleMA", config=None):
        super().__init__(name, config)
        self.short_window = self.config.get("short_window", 5)
        self.long_window = self.config.get("long_window", 20)

    def calculate_signals(self, df):
        """
        Calculate indicators and check for crossover.
        """
        if len(df) < self.long_window:
            return None

        # Add indicators using engine (it adds MA5, MA20 etc. by default)
        # If config windows differ from defaults, we calculate manually here for flexibility
        # But for now, let's assume we use standard TA-Lib calls if engine doesn't cover custom windows
        
        # Using IndicatorEngine for standard windows, or manual for custom
        # To support optimization, we should calculate specific windows here
        import talib
        close = df['close'].astype(float)
        
        short_ma = talib.SMA(close, timeperiod=self.short_window)
        long_ma = talib.SMA(close, timeperiod=self.long_window)
        
        # Get latest values
        current_short = short_ma.iloc[-1]
        current_long = long_ma.iloc[-1]
        
        # Get previous values (for crossover check)
        prev_short = short_ma.iloc[-2]
        prev_long = long_ma.iloc[-2]
        
        signal = None
        # Golden Cross
        if prev_short <= prev_long and current_short > current_long:
            signal = "BUY"
            self.logger.info(f"Golden Cross! MA{self.short_window}: {current_short} > MA{self.long_window}: {current_long}")
            
        # Dead Cross
        elif prev_short >= prev_long and current_short < current_long:
            signal = "SELL"
            self.logger.info(f"Dead Cross! MA{self.short_window}: {current_short} < MA{self.long_window}: {current_long}")
            
        return signal

    async def on_realtime_data(self, data):
        pass

    async def on_candle_close(self, candle):
        pass

class RSIStrategy(StrategyInterface):
    """
    RSI Mean Reversion Strategy.
    """
    def __init__(self, name="RSI", config=None):
        super().__init__(name, config)
        self.period = self.config.get("period", 14)
        self.buy_threshold = self.config.get("buy_threshold", 30)
        self.sell_threshold = self.config.get("sell_threshold", 70)

    def calculate_signals(self, df):
        if len(df) < self.period + 1:
            return None
            
        import talib
        close = df['close'].astype(float)
        rsi = talib.RSI(close, timeperiod=self.period)
        
        current_rsi = rsi.iloc[-1]
        prev_rsi = rsi.iloc[-2]
        
        signal = None
        # Buy Signal: RSI crosses below buy threshold (Oversold) -> Reversal or just below?
        # Usually Mean Reversion buys when it dips below.
        if current_rsi < self.buy_threshold:
             # To avoid repeated signals, maybe check if it WAS above threshold? 
             # For simplicity: Buy if in oversold zone
             signal = "BUY"
             self.logger.info(f"RSI Oversold! Value: {current_rsi}")
             
        # Sell Signal: RSI crosses above sell threshold (Overbought)
        elif current_rsi > self.sell_threshold:
            signal = "SELL"
            self.logger.info(f"RSI Overbought! Value: {current_rsi}")
            
        return signal

    async def on_realtime_data(self, data):
        pass

    async def on_candle_close(self, candle):
        pass

class BollingerBandStrategy(StrategyInterface):
    """
    Bollinger Band Mean Reversion Strategy.
    """
    def __init__(self, name="Bollinger", config=None):
        super().__init__(name, config)
        self.period = self.config.get("period", 20)
        self.std_dev = self.config.get("std_dev", 2.0)

    def calculate_signals(self, df):
        if len(df) < self.period:
            return None
            
        import talib
        close = df['close'].astype(float)
        upper, middle, lower = talib.BBANDS(close, timeperiod=self.period, nbdevup=self.std_dev, nbdevdn=self.std_dev, matype=0)
        
        current_price = close.iloc[-1]
        current_lower = lower.iloc[-1]
        current_upper = upper.iloc[-1]
        
        signal = None
        if current_price < current_lower:
            signal = "BUY"
            self.logger.info(f"Price below Lower Band! Price: {current_price}, Lower: {current_lower}")
        elif current_price > current_upper:
            signal = "SELL"
            self.logger.info(f"Price above Upper Band! Price: {current_price}, Upper: {current_upper}")
            
        return signal

    async def on_realtime_data(self, data):
        pass

    async def on_candle_close(self, candle):
        pass

class MACDStrategy(StrategyInterface):
    """
    MACD Trend Following Strategy.
    """
    def __init__(self, name="MACD", config=None):
        super().__init__(name, config)
        self.fast_period = self.config.get("fast", 12)
        self.slow_period = self.config.get("slow", 26)
        self.signal_period = self.config.get("signal", 9)

    def calculate_signals(self, df):
        if len(df) < self.slow_period + self.signal_period:
            return None
            
        import talib
        close = df['close'].astype(float)
        macd, macd_signal, macd_hist = talib.MACD(close, fastperiod=self.fast_period, slowperiod=self.slow_period, signalperiod=self.signal_period)
        
        current_macd = macd.iloc[-1]
        current_signal = macd_signal.iloc[-1]
        
        prev_macd = macd.iloc[-2]
        prev_signal = macd_signal.iloc[-2]
        
        signal = None
        # Golden Cross (MACD crosses above Signal)
        if prev_macd <= prev_signal and current_macd > current_signal:
            signal = "BUY"
            self.logger.info(f"MACD Golden Cross! MACD: {current_macd} > Signal: {current_signal}")
            
        # Dead Cross (MACD crosses below Signal)
        elif prev_macd >= prev_signal and current_macd < current_signal:
            signal = "SELL"
            self.logger.info(f"MACD Dead Cross! MACD: {current_macd} < Signal: {current_signal}")
            
        return signal

    async def on_realtime_data(self, data):
        pass

    async def on_candle_close(self, candle):
        pass
