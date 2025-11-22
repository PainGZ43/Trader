"""
AI Predictor - Advanced Version
LSTM + XGBoost + Sentiment 앙상블 기반 고급 예측기
"""
import random
import numpy as np
import pandas as pd
from logger import logger
from ai.ensemble_predictor import EnsemblePredictor
from ai.indicators import IndicatorCalculator

class AIPredictor:
    """고급 AI 예측기 - 앙상블 기반"""
    
    def __init__(self):
        self.ensemble = None
        self.use_ensemble = True
        self.lookback = 100
        self.lookback = 100
        self.recent_data = []  # 최근 데이터 저장 (LSTM용)
        self.scaler = None
        
        # Scaler 로드
        self.load_scaler()
        
        try:
            # 앙상블 모델 초기화
            self.ensemble = EnsemblePredictor()
            
            if self.ensemble.is_ready():
                logger.info("[SUCCESS] Advanced AI Predictor initialized with Ensemble models")

                self.use_ensemble = True
            else:
                logger.warning("[WARNING] Ensemble models not ready. Using fallback mock predictor")

                self.use_ensemble = False
        except Exception as e:
            logger.error(f"Failed to initialize Ensemble: {e}")
            logger.warning("Using mock predictor as fallback")
            self.use_ensemble = False
            
    def load_scaler(self):
        """Scaler 로드"""
        import joblib
        import os
        try:
            path = 'models/scaler.pkl'
            if os.path.exists(path):
                self.scaler = joblib.load(path)
                logger.info(f"Scaler loaded from {path}")
            else:
                logger.warning(f"Scaler not found at {path}")
        except Exception as e:
            logger.error(f"Failed to load scaler: {e}")
    
    def update_data(self, market_data):
        """
        시장 데이터 업데이트 (LSTM용 시퀀스 구축)
        
        Args:
            market_data: dict with OHLCV data
        """
        # OHLCV 데이터 추가
        self.recent_data.append(market_data)
        
        # 최대 lookback + 여유분만 유지
        if len(self.recent_data) > self.lookback + 100:
            self.recent_data = self.recent_data[-(self.lookback + 100):]
    
    def predict(self, market_data):
        """
        주가 상승 확률 예측
        
        Args:
            market_data: dict with keys like 'open', 'high', 'low', 'close', 'volume', 'change'
        
        Returns:
            score: 0.0 ~ 1.0 (높을수록 상승 확률 높음)
        """
        # 데이터 업데이트
        self.update_data(market_data)
        
        if self.use_ensemble and len(self.recent_data) >= self.lookback:
            try:
                return self._ensemble_predict(market_data)
            except Exception as e:
                logger.error(f"Ensemble prediction failed: {e}")
                logger.warning("Falling back to mock predictor")
                return self._mock_predict(market_data)
        else:
            # 데이터 부족하거나 앙상블 사용 불가시 Mock 사용
            return self._mock_predict(market_data)
    
    def _ensemble_predict(self, market_data):
        """앙상블 예측 (동기 버전)"""
        # 1. 최근 데이터를 DataFrame으로 변환
        df = pd.DataFrame(self.recent_data[-self.lookback - 60:])  # 지표 계산을 위해 여유분 추가
        
        # 필수 컬럼 확인
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in df.columns:
                logger.warning(f"Missing column: {col}. Using mock predictor")
                return self._mock_predict(market_data)
        
        # 2. 기술적 지표 계산
        df = IndicatorCalculator.calculate_all(df)
        df = df.dropna()
        
        if len(df) < self.lookback:
            logger.warning(f"Insufficient data after indicators: {len(df)}/{self.lookback}")
            return self._mock_predict(market_data)
        
        # 3. LSTM 입력 준비 (최근 lookback개)
        feature_cols = IndicatorCalculator.get_feature_names()
        lstm_input = df[feature_cols].iloc[-self.lookback:].values
        
        # 정규화 (저장된 Scaler 사용)
        if self.scaler:
            try:
                lstm_input = self.scaler.transform(lstm_input)
            except Exception as e:
                logger.error(f"Scaling failed: {e}")
                return self._mock_predict(market_data)
        else:
            logger.warning("Scaler not loaded. Using mock predictor.")
            return self._mock_predict(market_data)
        
        # 4. XGBoost 입력 준비 (현재 시점)
        xgboost_input = df[feature_cols].iloc[-1].values
        
        # 5. 앙상블 예측 (동기 버전 - 감성분석 제외)
        score = self.ensemble.predict_sync(lstm_input, xgboost_input)
        
        logger.debug(f"Ensemble prediction: {score:.4f}")
        
        return score
    
    def _mock_predict(self, market_data):
        """Mock 예측 (Fallback)"""
        # Simulation: Random score with slight bias if price is up
        change = market_data.get('change', 0)
        base_score = 0.5
        if change > 0:
            base_score += 0.1
        elif change < 0:
            base_score -= 0.1
            
        score = base_score + random.uniform(-0.2, 0.2)
        return max(0.0, min(1.0, score))
    
    def train(self, data):
        """
        모델 재학습 (Placeholder)
        실제 재학습은 train_ai.py 스크립트 사용
        """
        logger.info("Train method called. Use train_ai.py script for actual training.")
        logger.info("Command: python train_ai.py [stock_code] [period] [interval]")
        
    def get_status(self):
        """
        AI 시스템 상태 반환
        
        Returns:
            dict with status info
        """
        status = {
            'use_ensemble': self.use_ensemble,
            'data_points': len(self.recent_data),
            'lookback_required': self.lookback,
            'ready': len(self.recent_data) >= self.lookback
        }
        
        if self.ensemble:
            status['lstm_loaded'] = self.ensemble.lstm_loaded
            status['xgboost_loaded'] = self.ensemble.xgboost_loaded
        
        return status
