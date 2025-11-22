"""
AI Model Trainer
"""
from logger import logger
from ai.data_collector import DataCollector
from ai.indicators import IndicatorCalculator
from ai.indicators import IndicatorCalculator
from ai.lstm_model import LSTMPredictor, TENSORFLOW_AVAILABLE
from ai.xgboost_model import XGBoostPredictor
import numpy as np

class AITrainer:
    """AI 모델 학습 관리 클래스"""
    
    def train_models(self, stock_code='005930', period='1y', interval='1h'):
        """
        AI 모델 학습
        
        Args:
            stock_code: 종목 코드
            period: 기간
            interval: 간격
        """
        logger.info("=" * 60)
        logger.info("AI Model Training Started")
        logger.info("=" * 60)
        
        # 1. 데이터 수집
        logger.info(f"Step 1: Collecting data for {stock_code}...")
        collector = DataCollector()
        
        # 한국 종목코드 변환
        yf_symbol = DataCollector.convert_korean_code(stock_code)
        
        # 데이터 다운로드
        df = collector.get_stock_data(yf_symbol, period=period, interval=interval, use_cache=False)
        
        if df is None or len(df) < 1000:
            logger.error("Insufficient data for training!")
            return False
        
        logger.info(f"Data collected: {len(df)} rows")
        
        # 2. 기술적 지표 계산
        logger.info("Step 2: Calculating technical indicators...")
        df = IndicatorCalculator.calculate_all(df)
        
        # NaN 제거
        df = df.dropna()
        logger.info(f"Data after indicators: {len(df)} rows")
        
        if len(df) < 500:
            logger.error("Insufficient data after indicator calculation!")
            return False
        
        # 3. LSTM 데이터 준비 및 학습
        logger.info("Step 3: Training LSTM model...")
        
        lookback = 100
        X_lstm, y_lstm, scaler = collector.prepare_training_data(df, lookback=lookback)
        
        if len(X_lstm) < 100:
            logger.error("Insufficient sequences for LSTM training!")
            return False
        
        if TENSORFLOW_AVAILABLE:
            lstm_model = LSTMPredictor(lookback=lookback, n_features=X_lstm.shape[2])
            lstm_history = lstm_model.train(X_lstm, y_lstm, epochs=30, batch_size=32)
        else:
            logger.warning("TensorFlow not available. Skipping LSTM training.")
            lstm_model = None
        
        # Scaler 저장 (중요: Inference 시 동일한 스케일링 적용을 위해)
        collector.save_scaler(scaler, 'models/scaler.pkl')
        
        # 4. XGBoost 데이터 준비 및 학습
        logger.info("Step 4: Training XGBoost model...")
        
        # 특징 추출
        feature_cols = IndicatorCalculator.get_feature_names()
        X_xgb = df[feature_cols].values
        y_xgb = (df['close'].shift(-1) > df['close']).astype(int).values
        
        # 마지막 NaN 제거
        mask = ~np.isnan(y_xgb)
        X_xgb = X_xgb[mask]
        y_xgb = y_xgb[mask]
        
        xgboost_model = XGBoostPredictor()
        xgb_metrics = xgboost_model.train(X_xgb, y_xgb)
        
        # Feature Importance 확인
        try:
            xgboost_model.get_feature_importance()
        except Exception as e:
            logger.warning(f"Could not display feature importance: {e}")
        
        # 5. 결과 요약
        logger.info("=" * 60)
        logger.info("Training Completed!")
        logger.info("=" * 60)
        if lstm_model:
            logger.info(f"LSTM Model: {lstm_model.model_path}")
        else:
            logger.info("LSTM Model: Skipped (TensorFlow missing)")
        logger.info(f"XGBoost Model: {xgboost_model.model_path}")
        logger.info(f"XGBoost Accuracy: {xgb_metrics['accuracy']:.4f}")
        logger.info(f"XGBoost AUC: {xgb_metrics['auc']:.4f}")
        logger.info("=" * 60)
        
        return True
