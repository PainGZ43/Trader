import pandas as pd
import talib
from enum import Enum
from typing import Dict, Any

class MarketRegime(Enum):
    BULL = "BULL"
    BEAR = "BEAR"
    SIDEWAY = "SIDEWAY"
    VOLATILE = "VOLATILE"
    UNKNOWN = "UNKNOWN"

class MarketRegimeDetector:
    """
    Detects the current market regime based on technical indicators.
    """
    def __init__(self):
        pass

    def detect(self, df: pd.DataFrame) -> MarketRegime:
        """
        Detect regime from OHLCV DataFrame.
        Requires at least 30 rows for MA and ADX calculation.
        """
        if len(df) < 30:
            return MarketRegime.UNKNOWN

        df = df.copy()
        
        # Calculate Indicators
        # 1. Trend Strength (ADX)
        df['adx'] = talib.ADX(df['high'], df['low'], df['close'], timeperiod=14)
        current_adx = df['adx'].iloc[-1]
        
        # 2. Trend Direction (MA)
        df['ma20'] = talib.SMA(df['close'], timeperiod=20)
        df['ma60'] = talib.SMA(df['close'], timeperiod=60)
        
        current_close = df['close'].iloc[-1]
        ma20 = df['ma20'].iloc[-1]
        ma60 = df['ma60'].iloc[-1]
        
        # 3. Volatility (ATR)
        df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
        current_atr = df['atr'].iloc[-1]
        volatility_ratio = current_atr / current_close
        
        # Logic
        
        # High Volatility Check (e.g., > 2%)
        if volatility_ratio > 0.02:
            return MarketRegime.VOLATILE
            
        # Trending Check (ADX > 25)
        if current_adx > 25:
            if ma20 > ma60 and current_close > ma20:
                return MarketRegime.BULL
            elif ma20 < ma60 and current_close < ma20:
                return MarketRegime.BEAR
        
        # If not trending or volatile, it's sideway
        return MarketRegime.SIDEWAY
