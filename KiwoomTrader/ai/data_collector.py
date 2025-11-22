"""
Historical Data Collector
yfinance를 사용하여 실제 과거 주가 데이터 수집
"""
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from logger import logger
import os
import numpy as np
import joblib

class DataCollector:
    """과거 데이터 수집 클래스"""
    
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
    
    def download_stock_data(self, symbol, period='1y', interval='1m'):
        """
        주식 데이터 다운로드
        
        Args:
            symbol: 종목 코드 (예: '005930.KS' for 삼성전자)
            period: 기간 ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', 'max')
            interval: 간격 ('1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo')
        
        Returns:
            DataFrame with OHLCV data
        """
        logger.info(f"Downloading {symbol} data (period={period}, interval={interval})...")
        
        # Smart Period Adjustment for yfinance limits
        original_period = period
        if interval == '1m':
            if period in ['1mo', '3mo', '6mo', '1y', '2y', '5y', 'max']:
                logger.warning(f"1m data is limited to 7 days. Adjusting period {period} -> 5d")
                period = '5d'
        elif interval in ['2m', '5m', '15m', '30m', '90m']:
            if period in ['3mo', '6mo', '1y', '2y', '5y', 'max']:
                logger.warning(f"{interval} data is limited to 60 days. Adjusting period {period} -> 1mo")
                period = '1mo'
                
        if period != original_period:
            logger.info(f"Adjusted period to {period} due to yfinance limits")
        
        try:
            # yfinance로 데이터 다운로드
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                logger.error(f"No data found for {symbol}")
                return None
            
            # 컬럼명을 소문자로 변경
            df.columns = [col.lower() for col in df.columns]
            
            # 필요한 컬럼만 선택
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            df = df[required_cols]
            
            # NaN 제거
            df = df.dropna()
            
            logger.info(f"Downloaded {len(df)} rows for {symbol}")
            
            # CSV로 저장
            filename = f"{self.data_dir}/{symbol}_{period}_{interval}.csv"
            df.to_csv(filename)
            logger.info(f"Saved to {filename}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error downloading data for {symbol}: {e}")
            return None
    
    def load_cached_data(self, symbol, period='1y', interval='1m'):
        """
        캐시된 데이터 로드
        
        Returns:
            DataFrame or None
        """
        filename = f"{self.data_dir}/{symbol}_{period}_{interval}.csv"
        
        if os.path.exists(filename):
            logger.info(f"Loading cached data from {filename}")
            df = pd.read_csv(filename, index_col=0, parse_dates=True)
            return df
        else:
            return None
    
    def get_stock_data(self, symbol, period='1y', interval='1m', use_cache=True):
        """
        주식 데이터 가져오기 (캐시 우선)
        
        Args:
            symbol: 종목 코드
            period: 기간
            interval: 간격
            use_cache: 캐시 사용 여부
        
        Returns:
            DataFrame
        """
        if use_cache:
            cached_data = self.load_cached_data(symbol, period, interval)
            if cached_data is not None:
                return cached_data
        
        return self.download_stock_data(symbol, period, interval)
    
    def prepare_training_data(self, df, lookback=100):
        """
        학습 데이터 준비
        
        Args:
            df: OHLCV DataFrame with indicators
            lookback: 시퀀스 길이
        
        Returns:
            X: (samples, lookback, features)
            y: (samples,) - 다음 캔들 상승(1) / 하락(0)
        """
        # 타겟 생성: 다음 캔들이 상승하면 1, 하락하면 0
        df['target'] = (df['close'].shift(-1) > df['close']).astype(int)
        
        # NaN 제거
        df = df.dropna()
        
        # 특징 컬럼 선택
        from ai.indicators import IndicatorCalculator
        feature_cols = IndicatorCalculator.get_feature_names()
        
        # 정규화 (MinMaxScaling)
        from sklearn.preprocessing import MinMaxScaler
        scaler = MinMaxScaler()
        
        # 특징만 정규화
        df_scaled = df.copy()
        df_scaled[feature_cols] = scaler.fit_transform(df[feature_cols])
        
        X_list = []
        y_list = []
        
        # 시퀀스 생성
        for i in range(lookback, len(df_scaled)):
            X_list.append(df_scaled[feature_cols].iloc[i-lookback:i].values)
            y_list.append(df_scaled['target'].iloc[i])
        
        X = np.array(X_list)
        y = np.array(y_list)
        
        logger.info(f"Prepared training data: X shape={X.shape}, y shape={y.shape}")
        
        return X, y, scaler
    
    @staticmethod
    def convert_korean_code(code):
        """
        한국 종목코드를 y finance 형식으로 변환
        
        Args:
            code: 종목코드 (예: '005930')
        
        Returns:
            yfinance 형식 (예: '005930.KS')
        """
        return f"{code}.KS"

    def save_scaler(self, scaler, path='models/scaler.pkl'):
        """Scaler 저장"""
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            joblib.dump(scaler, path)
            logger.info(f"Scaler saved to {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save scaler: {e}")
            return False

    def load_scaler(self, path='models/scaler.pkl'):
        """Scaler 로드"""
        try:
            if os.path.exists(path):
                scaler = joblib.load(path)
                logger.info(f"Scaler loaded from {path}")
                return scaler
            else:
                logger.warning(f"Scaler not found at {path}")
                return None
        except Exception as e:
            logger.error(f"Failed to load scaler: {e}")
            return None
