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

indicator_engine = IndicatorEngine()
