import pandas as pd
import talib
from core.logger import get_logger

class IndicatorEngine:
    """
    Technical Analysis Engine using TA-Lib.
    Calculates indicators for DataFrames.
    """
    def __init__(self):
        self.logger = get_logger("IndicatorEngine")

    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add standard indicators to the DataFrame.
        Expects columns: 'open', 'high', 'low', 'close', 'volume'
        """
        try:
            if df.empty:
                return df

            # Ensure columns are float
            close = df['close'].astype(float)
            high = df['high'].astype(float)
            low = df['low'].astype(float)
            volume = df['volume'].astype(float)

            # 1. Moving Averages
            df['MA5'] = talib.SMA(close, timeperiod=5)
            df['MA20'] = talib.SMA(close, timeperiod=20)
            df['MA60'] = talib.SMA(close, timeperiod=60)
            df['MA120'] = talib.SMA(close, timeperiod=120)

            # 2. RSI
            df['RSI14'] = talib.RSI(close, timeperiod=14)

            # 3. Bollinger Bands
            upper, middle, lower = talib.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
            df['BB_UPPER'] = upper
            df['BB_MIDDLE'] = middle
            df['BB_LOWER'] = lower

            # 4. MACD
            macd, macdsignal, macdhist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
            df['MACD'] = macd
            df['MACD_SIGNAL'] = macdsignal
            df['MACD_HIST'] = macdhist

            # 5. Volatility (ATR)
            df['ATR14'] = talib.ATR(high, low, close, timeperiod=14)

            return df

        except Exception as e:
            self.logger.error(f"Indicator calculation failed: {e}")
            return df

    def get_indicator(self, df: pd.DataFrame, name: str, **kwargs) -> pd.Series:
        """
        Calculate and return a specific indicator series.
        """
        try:
            if df.empty:
                return pd.Series()

            close = df['close'].astype(float)
            high = df['high'].astype(float)
            low = df['low'].astype(float)

            if name == "SMA":
                period = kwargs.get("timeperiod", 20)
                return talib.SMA(close, timeperiod=period)
            
            elif name == "ADX":
                period = kwargs.get("timeperiod", 14)
                return talib.ADX(high, low, close, timeperiod=period)
            
            elif name == "ATR":
                period = kwargs.get("timeperiod", 14)
                return talib.ATR(high, low, close, timeperiod=period)
            
            elif name == "RSI":
                period = kwargs.get("timeperiod", 14)
                return talib.RSI(close, timeperiod=period)

            elif name == "MACD":
                fast = kwargs.get("fastperiod", 12)
                slow = kwargs.get("slowperiod", 26)
                signal = kwargs.get("signalperiod", 9)
                macd, macdsignal, macdhist = talib.MACD(close, fastperiod=fast, slowperiod=slow, signalperiod=signal)
                return {"macd": macd, "signal": macdsignal, "hist": macdhist}

            elif name == "BBANDS":
                period = kwargs.get("timeperiod", 20)
                nbdevup = kwargs.get("nbdevup", 2)
                nbdevdn = kwargs.get("nbdevdn", 2)
                upper, middle, lower = talib.BBANDS(close, timeperiod=period, nbdevup=nbdevup, nbdevdn=nbdevdn, matype=0)
                return {"upper": upper, "middle": middle, "lower": lower}

            elif name == "STOCH":
                fastk_period = kwargs.get("fastk_period", 5)
                slowk_period = kwargs.get("slowk_period", 3)
                slowk_matype = kwargs.get("slowk_matype", 0)
                slowd_period = kwargs.get("slowd_period", 3)
                slowd_matype = kwargs.get("slowd_matype", 0)
                
                slowk, slowd = talib.STOCH(high, low, close, 
                                           fastk_period=fastk_period, 
                                           slowk_period=slowk_period, 
                                           slowk_matype=slowk_matype, 
                                           slowd_period=slowd_period, 
                                           slowd_matype=slowd_matype)
                return {"k": slowk, "d": slowd}

            else:
                self.logger.warning(f"Unknown indicator requested: {name}")
                return pd.Series()

        except Exception as e:
            self.logger.error(f"Error getting indicator {name}: {e}")
            return pd.Series()

indicator_engine = IndicatorEngine()
