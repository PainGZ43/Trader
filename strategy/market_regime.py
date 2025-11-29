import pandas as pd
from enum import Enum
from typing import Dict, Any, Optional
from core.logger import get_logger
from data.indicator_engine import IndicatorEngine

class MarketRegime(Enum):
    BULL = "BULL"
    BEAR = "BEAR"
    SIDEWAY = "SIDEWAY"
    VOLATILE = "VOLATILE"
    UNKNOWN = "UNKNOWN"

class MarketRegimeDetector:
    """
    Detects the current market regime based on technical indicators.
    Uses ADX (Trend Strength), Moving Averages (Trend Direction), and ATR (Volatility).
    """
    
    def __init__(self):
        self.logger = get_logger("MarketRegimeDetector")
        self.indicator_engine = IndicatorEngine()
        
        # Parameters
        self.adx_period = 14
        self.adx_threshold = 25
        self.ma_short_period = 20
        self.ma_long_period = 60
        self.volatility_threshold = 0.02 # 2% daily range

    def detect(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze the market regime for the given OHLCV DataFrame.
        
        Args:
            df: DataFrame with 'open', 'high', 'low', 'close', 'volume' columns.
            
        Returns:
            Dict containing 'regime' (MarketRegime), 'confidence', 'details', 'indicators'.
        """
        if df is None or len(df) < self.ma_long_period:
            return {
                "regime": MarketRegime.UNKNOWN,
                "confidence": 0.0,
                "details": "Insufficient data",
                "indicators": {}
            }

        try:
            # 1. Calculate Indicators using IndicatorEngine
            # ADX
            adx_series = self.indicator_engine.get_indicator(df, "ADX", timeperiod=self.adx_period)
            current_adx = adx_series.iloc[-1] if not adx_series.empty else 0
            
            # Moving Averages
            ma_short = self.indicator_engine.get_indicator(df, "SMA", timeperiod=self.ma_short_period)
            ma_long = self.indicator_engine.get_indicator(df, "SMA", timeperiod=self.ma_long_period)
            
            # ATR for Volatility
            atr_series = self.indicator_engine.get_indicator(df, "ATR", timeperiod=14)
            current_atr = atr_series.iloc[-1] if not atr_series.empty else 0
            
            current_price = df['close'].iloc[-1]
            current_ma_short = ma_short.iloc[-1]
            current_ma_long = ma_long.iloc[-1]
            
            # Volatility Ratio (ATR / Price)
            volatility_ratio = current_atr / current_price if current_price > 0 else 0

            # 2. Determine Regime
            regime = MarketRegime.SIDEWAY
            confidence = 0.5 # Default confidence for sideway
            details = "Market is ranging"

            # Logic
            if volatility_ratio > self.volatility_threshold:
                regime = MarketRegime.VOLATILE
                confidence = min(volatility_ratio * 50, 1.0) # Scale confidence
                details = f"High Volatility ({volatility_ratio:.2%})"
            
            elif current_adx >= self.adx_threshold:
                # Trending
                if current_price > current_ma_short and current_ma_short > current_ma_long:
                    regime = MarketRegime.BULL
                    confidence = min(current_adx / 50.0, 1.0)
                    details = "Strong Bull Trend"
                elif current_price < current_ma_short and current_ma_short < current_ma_long:
                    regime = MarketRegime.BEAR
                    confidence = min(current_adx / 50.0, 1.0)
                    details = "Strong Bear Trend"
            
            result = {
                "regime": regime,
                "confidence": round(confidence, 2),
                "details": details,
                "indicators": {
                    "adx": round(current_adx, 2),
                    "ma_short": round(current_ma_short, 2),
                    "ma_long": round(current_ma_long, 2),
                    "atr_ratio": round(volatility_ratio, 4),
                    "price": float(current_price)
                },
                "timestamp": df.index[-1] if not df.empty else None
            }
            
            self.logger.debug(f"Market Regime: {regime.value} ({details})")
            return result

        except Exception as e:
            self.logger.error(f"Error analyzing market regime: {e}")
            return {
                "regime": MarketRegime.UNKNOWN,
                "confidence": 0.0,
                "details": str(e),
                "indicators": {}
            }
