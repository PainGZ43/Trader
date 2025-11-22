"""
Technical Indicators Calculator
다양한 기술적 지표를 계산하는 모듈
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg') # Force Agg backend
from logger import logger

class IndicatorCalculator:
    """기술적 지표 계산 클래스"""
    
    @staticmethod
    def calculate_all(df):
        """
        모든 기술적 지표 계산
        
        Args:
            df: DataFrame with columns ['open', 'high', 'low', 'close', 'volume']
        
        Returns:
            DataFrame with all technical indicators added
        """
        result = df.copy()
        
        # Trend Indicators
        result = IndicatorCalculator.add_moving_averages(result)
        result = IndicatorCalculator.add_macd(result)
        
        # Momentum Indicators
        result = IndicatorCalculator.add_rsi(result)
        result = IndicatorCalculator.add_stochastic(result)
        result = IndicatorCalculator.add_momentum(result)
        
        # Volatility Indicators
        result = IndicatorCalculator.add_bollinger_bands(result)
        result = IndicatorCalculator.add_atr(result)
        
        # Volume Indicators
        result = IndicatorCalculator.add_volume_indicators(result)
        
        return result
    
    @staticmethod
    def add_moving_averages(df):
        """이동평균선 추가"""
        df['SMA_5'] = df['close'].rolling(window=5).mean()
        df['SMA_10'] = df['close'].rolling(window=10).mean()
        df['SMA_20'] = df['close'].rolling(window=20).mean()
        df['SMA_60'] = df['close'].rolling(window=60).mean()
        
        df['EMA_5'] = df['close'].ewm(span=5, adjust=False).mean()
        df['EMA_10'] = df['close'].ewm(span=10, adjust=False).mean()
        df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
        
        return df
    
    @staticmethod
    def add_rsi(df, period=14):
        """RSI (Relative Strength Index) 추가"""
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        return df
    
    @staticmethod
    def add_macd(df, fast=12, slow=26, signal=9):
        """MACD 추가"""
        exp1 = df['close'].ewm(span=fast, adjust=False).mean()
        exp2 = df['close'].ewm(span=slow, adjust=False).mean()
        
        df['MACD'] = exp1 - exp2
        df['MACD_Signal'] = df['MACD'].ewm(span=signal, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
        
        return df
    
    @staticmethod
    def add_bollinger_bands(df, period=20, std_dev=2):
        """볼린저 밴드 추가"""
        df['BB_Middle'] = df['close'].rolling(window=period).mean()
        std = df['close'].rolling(window=period).std()
        
        df['BB_Upper'] = df['BB_Middle'] + (std * std_dev)
        df['BB_Lower'] = df['BB_Middle'] - (std * std_dev)
        df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']
        df['BB_Position'] = (df['close'] - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'])
        
        return df
    
    @staticmethod
    def add_stochastic(df, k_period=14, d_period=3):
        """스토캐스틱 오실레이터 추가"""
        low_min = df['low'].rolling(window=k_period).min()
        high_max = df['high'].rolling(window=k_period).max()
        
        df['Stoch_K'] = 100 * (df['close'] - low_min) / (high_max - low_min)
        df['Stoch_D'] = df['Stoch_K'].rolling(window=d_period).mean()
        
        return df
    
    @staticmethod
    def add_atr(df, period=14):
        """ATR (Average True Range) 추가"""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['ATR'] = true_range.rolling(window=period).mean()
        df['ATR_Ratio'] = df['ATR'] / df['close']
        
        return df
    
    @staticmethod
    def add_momentum(df):
        """모멘텀 지표 추가"""
        # Rate of Change
        df['ROC_5'] = ((df['close'] - df['close'].shift(5)) / df['close'].shift(5)) * 100
        df['ROC_10'] = ((df['close'] - df['close'].shift(10)) / df['close'].shift(10)) * 100
        
        # Price momentum
        df['Momentum_5'] = df['close'] - df['close'].shift(5)
        df['Momentum_10'] = df['close'] - df['close'].shift(10)
        
        return df
    
    @staticmethod
    def add_volume_indicators(df):
        """거래량 지표 추가"""
        # Volume SMA
        df['Volume_SMA_20'] = df['volume'].rolling(window=20).mean()
        df['Volume_Ratio'] = df['volume'] / df['Volume_SMA_20']
        
        # OBV (On-Balance Volume)
        obv = [0]
        for i in range(1, len(df)):
            if df['close'].iloc[i] > df['close'].iloc[i-1]:
                obv.append(obv[-1] + df['volume'].iloc[i])
            elif df['close'].iloc[i] < df['close'].iloc[i-1]:
                obv.append(obv[-1] - df['volume'].iloc[i])
            else:
                obv.append(obv[-1])
        
        df['OBV'] = obv
        df['OBV_EMA'] = df['OBV'].ewm(span=20, adjust=False).mean()
        
        return df
    
    @staticmethod
    def get_feature_names():
        """학습에 사용할 특징 이름 리스트"""
        return [
            'SMA_5', 'SMA_10', 'SMA_20', 'SMA_60',
            'EMA_5', 'EMA_10', 'EMA_20',
            'RSI', 'MACD', 'MACD_Signal', 'MACD_Hist',
            'BB_Width', 'BB_Position',
            'Stoch_K', 'Stoch_D',
            'ATR_Ratio',
            'ROC_5', 'ROC_10',
            'Momentum_5', 'Momentum_10',
            'Volume_Ratio', 'OBV_EMA'
        ]
