import pandas as pd
import talib
import numpy as np
from typing import Dict, Any, Optional
from strategy.base_strategy import BaseStrategy, Signal
from datetime import datetime

class VolatilityBreakoutStrategy(BaseStrategy):
    """
    래리 윌리엄스의 변동성 돌파 전략.
    매수: 현재가 > 시가 + (전일 변동폭 * k)
    """
    @classmethod
    def get_parameter_schema(cls) -> Dict[str, Dict[str, Any]]:
        return {
            "k": {
                "type": "float", 
                "min": 0.1, 
                "max": 1.0, 
                "default": 0.5, 
                "desc": "돌파 계수 (k)"
            }
        }

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
    이동평균선 골든크로스 / 데드크로스 전략.
    """
    @classmethod
    def get_parameter_schema(cls) -> Dict[str, Dict[str, Any]]:
        return {
            "short_window": {
                "type": "int", 
                "min": 3, 
                "max": 50, 
                "default": 5, 
                "desc": "단기 이평 기간"
            },
            "long_window": {
                "type": "int", 
                "min": 10, 
                "max": 200, 
                "default": 20, 
                "desc": "장기 이평 기간"
            }
        }

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
    RSI 역추세 (Mean Reversion) 전략.
    매수: RSI < 30 (과매도)
    매도: RSI > 70 (과매수)
    """
    @classmethod
    def get_parameter_schema(cls) -> Dict[str, Dict[str, Any]]:
        return {
            "period": {
                "type": "int", 
                "min": 5, 
                "max": 30, 
                "default": 14, 
                "desc": "RSI 기간"
            },
            "buy_threshold": {
                "type": "int", 
                "min": 10, 
                "max": 50, 
                "default": 30, 
                "desc": "매수 임계값"
            },
            "sell_threshold": {
                "type": "int", 
                "min": 50, 
                "max": 90, 
                "default": 70, 
                "desc": "매도 임계값"
            }
        }

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
    볼린저 밴드 전략.
    매수: 가격 < 하단 밴드
    매도: 가격 > 상단 밴드
    """
    @classmethod
    def get_parameter_schema(cls) -> Dict[str, Dict[str, Any]]:
        return {
            "period": {
                "type": "int", 
                "min": 10, 
                "max": 50, 
                "default": 20, 
                "desc": "밴드 기간"
            },
            "std_dev": {
                "type": "float", 
                "min": 1.0, 
                "max": 3.0, 
                "default": 2.0, 
                "desc": "표준편차 승수"
            }
        }

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

class MACDStrategy(BaseStrategy):
    """
    MACD 추세 추종 전략.
    매수: MACD > Signal (골든크로스)
    매도: MACD < Signal (데드크로스)
    """
    @classmethod
    def get_parameter_schema(cls) -> Dict[str, Dict[str, Any]]:
        return {
            "fast_period": {"type": "int", "min": 5, "max": 20, "default": 12, "desc": "단기 EMA 기간"},
            "slow_period": {"type": "int", "min": 20, "max": 50, "default": 26, "desc": "장기 EMA 기간"},
            "signal_period": {"type": "int", "min": 5, "max": 20, "default": 9, "desc": "시그널 기간"}
        }

    def __init__(self, strategy_id: str, symbol: str):
        super().__init__(strategy_id, symbol)
        self.fast_period = 12
        self.slow_period = 26
        self.signal_period = 9
        self.prices = []

    def initialize(self, config: Dict[str, Any]):
        super().initialize(config)
        self.fast_period = config.get("fast_period", 12)
        self.slow_period = config.get("slow_period", 26)
        self.signal_period = config.get("signal_period", 9)

    def calculate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        macd, signal, _ = talib.MACD(df['close'], 
                                     fastperiod=self.fast_period, 
                                     slowperiod=self.slow_period, 
                                     signalperiod=self.signal_period)
        df['macd'] = macd
        df['macd_signal'] = signal
        
        df['signal'] = 0
        # Buy: MACD crosses above Signal
        df.loc[(df['macd'] > df['macd_signal']) & (df['macd'].shift(1) <= df['macd_signal'].shift(1)), 'signal'] = 1
        # Sell: MACD crosses below Signal
        df.loc[(df['macd'] < df['macd_signal']) & (df['macd'].shift(1) >= df['macd_signal'].shift(1)), 'signal'] = -1
        
        return df

    def update_market_data(self, df: pd.DataFrame):
        if not df.empty:
            self.prices = df['close'].tolist()
            max_len = self.slow_period + self.signal_period + 10
            if len(self.prices) > max_len:
                self.prices = self.prices[-max_len:]

    async def on_realtime_data(self, data: Dict[str, Any]) -> Optional[Signal]:
        try:
            current_price = float(data.get('price', 0))
            self.prices.append(current_price)
            
            if len(self.prices) < self.slow_period + self.signal_period:
                return None
                
            closes = np.array(self.prices, dtype=float)
            macd, signal, _ = talib.MACD(closes, 
                                         fastperiod=self.fast_period, 
                                         slowperiod=self.slow_period, 
                                         signalperiod=self.signal_period)
            
            curr_macd = macd[-1]
            curr_signal = signal[-1]
            prev_macd = macd[-2]
            prev_signal = signal[-2]
            
            timestamp = datetime.now()
            
            # Buy
            if curr_macd > curr_signal and prev_macd <= prev_signal:
                if self.state.current_position == 0:
                    return Signal(self.symbol, 'BUY', current_price, timestamp, f"MACD Golden Cross ({curr_macd:.2f} > {curr_signal:.2f})")
            
            # Sell
            elif curr_macd < curr_signal and prev_macd >= prev_signal:
                if self.state.current_position > 0:
                    return Signal(self.symbol, 'SELL', current_price, timestamp, f"MACD Dead Cross ({curr_macd:.2f} < {curr_signal:.2f})")
                    
        except Exception as e:
            self.logger.error(f"Error in on_realtime_data: {e}")
        return None

class DualThrustStrategy(BaseStrategy):
    """
    Dual Thrust 전략.
    Range = Max(HH-LC, HC-LL)
    매수 = 시가 + Range * k1
    매도 = 시가 - Range * k2 (손절/숏)
    """
    @classmethod
    def get_parameter_schema(cls) -> Dict[str, Dict[str, Any]]:
        return {
            "n_days": {"type": "int", "min": 1, "max": 5, "default": 2, "desc": "기준 일수 (N일)"},
            "k1": {"type": "float", "min": 0.1, "max": 1.0, "default": 0.5, "desc": "매수 계수 (k1)"},
            "k2": {"type": "float", "min": 0.1, "max": 1.0, "default": 0.5, "desc": "매도 계수 (k2)"}
        }

    def __init__(self, strategy_id: str, symbol: str):
        super().__init__(strategy_id, symbol)
        self.n_days = 2
        self.k1 = 0.5
        self.k2 = 0.5

    def initialize(self, config: Dict[str, Any]):
        super().initialize(config)
        self.n_days = config.get("n_days", 2)
        self.k1 = config.get("k1", 0.5)
        self.k2 = config.get("k2", 0.5)

    def calculate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        # Calculate Range over N days
        df['hh'] = df['high'].rolling(window=self.n_days).max().shift(1)
        df['lc'] = df['close'].rolling(window=self.n_days).min().shift(1)
        df['hc'] = df['close'].rolling(window=self.n_days).max().shift(1)
        df['ll'] = df['low'].rolling(window=self.n_days).min().shift(1)
        
        df['range'] = np.maximum(df['hh'] - df['lc'], df['hc'] - df['ll'])
        
        df['buy_trigger'] = df['open'] + df['range'] * self.k1
        df['sell_trigger'] = df['open'] - df['range'] * self.k2
        
        df['signal'] = 0
        df.loc[df['high'] > df['buy_trigger'], 'signal'] = 1
        # In Long-only, sell trigger acts as stop loss or exit if price drops too much
        # Or we can treat it as: if price < sell_trigger, exit position
        df.loc[df['low'] < df['sell_trigger'], 'signal'] = -1
        
        return df

    def update_market_data(self, df: pd.DataFrame):
        if len(df) < self.n_days:
            return
            
        try:
            recent = df.iloc[-self.n_days:]
            hh = recent['high'].max()
            lc = recent['close'].min()
            hc = recent['close'].max()
            ll = recent['low'].min()
            
            rng = max(hh - lc, hc - ll)
            self.prev_range = rng
            self.logger.info(f"Dual Thrust Range: {rng}")
            
        except Exception as e:
            self.logger.error(f"Failed to update market data: {e}")

    async def on_realtime_data(self, data: Dict[str, Any]) -> Optional[Signal]:
        try:
            current_price = float(data.get('price', 0))
            daily_open = float(data.get('open', 0))
            
            if daily_open == 0 or not hasattr(self, 'prev_range'):
                return None
                
            buy_trigger = daily_open + self.prev_range * self.k1
            sell_trigger = daily_open - self.prev_range * self.k2
            
            timestamp = datetime.now()
            
            # Buy
            if current_price > buy_trigger:
                if self.state.current_position == 0:
                    return Signal(self.symbol, 'BUY', current_price, timestamp, f"Dual Thrust Breakout ({current_price} > {buy_trigger})")
            
            # Sell (Stop Loss logic for Long-only)
            elif current_price < sell_trigger:
                if self.state.current_position > 0:
                    return Signal(self.symbol, 'SELL', current_price, timestamp, f"Dual Thrust Stop ({current_price} < {sell_trigger})")
                    
        except Exception as e:
            self.logger.error(f"Error in on_realtime_data: {e}")
        return None

class RSI2Strategy(BaseStrategy):
    """
    Larry Connors의 RSI 2 전략 (단기 역추세).
    매수: 가격 > 200일 이평선 & RSI(2) < 10
    매도: 가격 > 5일 이평선
    """
    @classmethod
    def get_parameter_schema(cls) -> Dict[str, Dict[str, Any]]:
        return {
            "rsi_period": {"type": "int", "min": 2, "max": 5, "default": 2, "desc": "RSI 기간"},
            "ma_short": {"type": "int", "min": 3, "max": 10, "default": 5, "desc": "청산용 단기 이평"},
            "ma_long": {"type": "int", "min": 100, "max": 300, "default": 200, "desc": "추세용 장기 이평"},
            "rsi_lower": {"type": "int", "min": 5, "max": 20, "default": 10, "desc": "RSI 과매도 기준"}
        }

    def __init__(self, strategy_id: str, symbol: str):
        super().__init__(strategy_id, symbol)
        self.rsi_period = 2
        self.ma_short = 5
        self.ma_long = 200
        self.rsi_lower = 10
        self.prices = []

    def initialize(self, config: Dict[str, Any]):
        super().initialize(config)
        self.rsi_period = config.get("rsi_period", 2)
        self.ma_short = config.get("ma_short", 5)
        self.ma_long = config.get("ma_long", 200)
        self.rsi_lower = config.get("rsi_lower", 10)

    def calculate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['rsi'] = talib.RSI(df['close'], timeperiod=self.rsi_period)
        df['ma_short'] = talib.SMA(df['close'], timeperiod=self.ma_short)
        df['ma_long'] = talib.SMA(df['close'], timeperiod=self.ma_long)
        
        df['signal'] = 0
        # Buy: Close > MA200 AND RSI < 10
        df.loc[(df['close'] > df['ma_long']) & (df['rsi'] < self.rsi_lower), 'signal'] = 1
        # Sell: Close > MA5
        df.loc[df['close'] > df['ma_short'], 'signal'] = -1
        
        return df

    def update_market_data(self, df: pd.DataFrame):
        if not df.empty:
            self.prices = df['close'].tolist()
            max_len = self.ma_long + 10
            if len(self.prices) > max_len:
                self.prices = self.prices[-max_len:]

    async def on_realtime_data(self, data: Dict[str, Any]) -> Optional[Signal]:
        try:
            current_price = float(data.get('price', 0))
            self.prices.append(current_price)
            
            if len(self.prices) < self.ma_long:
                return None
                
            closes = np.array(self.prices, dtype=float)
            rsi = talib.RSI(closes, timeperiod=self.rsi_period)[-1]
            ma_short = talib.SMA(closes, timeperiod=self.ma_short)[-1]
            ma_long = talib.SMA(closes, timeperiod=self.ma_long)[-1]
            
            timestamp = datetime.now()
            
            # Buy
            if current_price > ma_long and rsi < self.rsi_lower:
                if self.state.current_position == 0:
                    return Signal(self.symbol, 'BUY', current_price, timestamp, f"RSI2 Oversold ({rsi:.1f} < {self.rsi_lower})")
            
            # Sell
            elif current_price > ma_short:
                if self.state.current_position > 0:
                    return Signal(self.symbol, 'SELL', current_price, timestamp, f"RSI2 Exit (Price > MA{self.ma_short})")
                    
        except Exception as e:
            self.logger.error(f"Error in on_realtime_data: {e}")
        return None

class EnvelopeStrategy(BaseStrategy):
    """
    엔벨로프 (Envelope) 전략.
    매수: 가격 < 하단 밴드
    매도: 가격 > 상단 밴드 (또는 중심선)
    """
    @classmethod
    def get_parameter_schema(cls) -> Dict[str, Dict[str, Any]]:
        return {
            "period": {"type": "int", "min": 10, "max": 50, "default": 20, "desc": "이평선 기간"},
            "rate": {"type": "float", "min": 1.0, "max": 20.0, "default": 5.0, "desc": "밴드 폭 (%)"}
        }

    def __init__(self, strategy_id: str, symbol: str):
        super().__init__(strategy_id, symbol)
        self.period = 20
        self.rate = 5.0 # 5%

    def initialize(self, config: Dict[str, Any]):
        super().initialize(config)
        self.period = config.get("period", 20)
        self.rate = config.get("rate", 5.0)

    def calculate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['ma'] = talib.SMA(df['close'], timeperiod=self.period)
        df['upper'] = df['ma'] * (1 + self.rate / 100)
        df['lower'] = df['ma'] * (1 - self.rate / 100)
        
        df['signal'] = 0
        df.loc[df['close'] < df['lower'], 'signal'] = 1
        df.loc[df['close'] > df['upper'], 'signal'] = -1
        
        return df

    def update_market_data(self, df: pd.DataFrame):
        # Envelope doesn't need much state other than MA calculation
        pass

    async def on_realtime_data(self, data: Dict[str, Any]) -> Optional[Signal]:
        # Not implemented for realtime yet
        return None
