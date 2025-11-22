"""
Ensemble Predictor
LSTM + XGBoost + Sentiment 앙상블 예측기
"""
import numpy as np
from logger import logger
from ai.lstm_model import LSTMPredictor
from ai.xgboost_model import XGBoostPredictor
from ai.sentiment import SentimentAnalyzer

class EnsemblePredictor:
    """앙상블 예측기 - LSTM + XGBoost + Sentiment"""
    
    def __init__(self, 
                 lstm_weight=0.40, 
                 xgboost_weight=0.35, 
                 sentiment_weight=0.25,
                 lstm_path='models/lstm_model.h5',
                 xgboost_path='models/xgboost_model.pkl'):
        """
        Args:
            lstm_weight: LSTM 모델 가중치
            xgboost_weight: XGBoost 모델 가중치
            sentiment_weight: 감성 분석 가중치
        """
        self.lstm_weight = lstm_weight
        self.xgboost_weight = xgboost_weight
        self.sentiment_weight = sentiment_weight
        
        # 모델 초기화
        self.lstm_model = LSTMPredictor(model_path=lstm_path)
        self.xgboost_model = XGBoostPredictor(model_path=xgboost_path)
        self.sentiment_analyzer = SentimentAnalyzer()
        
        # 모델 로드 시도
        self.lstm_loaded = self.lstm_model.load_model()
        self.xgboost_loaded = self.xgboost_model.load_model()
        
        logger.info(f"Ensemble Predictor initialized")
        logger.info(f"Weights: LSTM={lstm_weight}, XGBoost={xgboost_weight}, Sentiment={sentiment_weight}")
        logger.info(f"LSTM loaded: {self.lstm_loaded}, XGBoost loaded: {self.xgboost_loaded}")
    
    async def predict(self, lstm_input, xgboost_input, stock_code=None):
        """
        앙상블 예측 수행
        
        Args:
            lstm_input: (lookback, features) - LSTM 입력
            xgboost_input: (features,) - XGBoost 입력
            stock_code: 종목코드 (감성분석용)
        
        Returns:
            score: 최종 예측 점수 (0-1)
            details: 각 모델의 예측 상세
        """
        scores = {}
        weights_used = {}
        
        # 1. LSTM 예측
        if self.lstm_loaded:
            try:
                lstm_score = self.lstm_model.predict(lstm_input)[0]
                scores['lstm'] = lstm_score
                weights_used['lstm'] = self.lstm_weight
                logger.debug(f"LSTM score: {lstm_score:.4f}")
            except Exception as e:
                logger.warning(f"LSTM prediction failed: {e}")
                weights_used['lstm'] = 0
        else:
            logger.warning("LSTM model not loaded, skipping")
            weights_used['lstm'] = 0
        
        # 2. XGBoost 예측
        if self.xgboost_loaded:
            try:
                xgboost_score = self.xgboost_model.predict(xgboost_input)[0]
                scores['xgboost'] = xgboost_score
                weights_used['xgboost'] = self.xgboost_weight
                logger.debug(f"XGBoost score: {xgboost_score:.4f}")
            except Exception as e:
                logger.warning(f"XGBoost prediction failed: {e}")
                weights_used['xgboost'] = 0
        else:
            logger.warning("XGBoost model not loaded, skipping")
            weights_used['xgboost'] = 0
        
        # 3. Sentiment 분석
        if stock_code:
            try:
                sentiment_score = await self.sentiment_analyzer.get_sentiment_score(stock_code)
                # -1 ~ +1을 0 ~ 1로 정규화
                sentiment_score = (sentiment_score + 1) / 2
                scores['sentiment'] = sentiment_score
                weights_used['sentiment'] = self.sentiment_weight
                logger.debug(f"Sentiment score: {sentiment_score:.4f}")
            except Exception as e:
                logger.warning(f"Sentiment analysis failed: {e}")
                # 중립값 사용
                scores['sentiment'] = 0.5
                weights_used['sentiment'] = self.sentiment_weight
        else:
            # 종목코드 없으면 중립값
            scores['sentiment'] = 0.5
            weights_used['sentiment'] = self.sentiment_weight
        
        # 4. 가중 평균 계산
        total_weight = sum(weights_used.values())
        
        if total_weight == 0:
            logger.error("No models available for prediction!")
            return 0.5, {'error': 'No models loaded'}
        
        # 정규화된 가중치 적용
        final_score = sum(
            scores.get(model, 0.5) * (weight / total_weight)
            for model, weight in weights_used.items()
        )
        
        details = {
            'final_score': final_score,
            'lstm_score': scores.get('lstm', None),
            'xgboost_score': scores.get('xgboost', None),
            'sentiment_score': scores.get('sentiment', None),
            'weights_used': weights_used
        }
        
        logger.info(f"Ensemble prediction: {final_score:.4f} (LSTM: {scores.get('lstm', 'N/A')}, XGB: {scores.get('xgboost', 'N/A')}, Sent: {scores.get('sentiment', 'N/A')})")
        
        return final_score, details
    
    def predict_sync(self, lstm_input, xgboost_input, stock_code=None):
        """
        동기 버전 예측 (감성분석 제외)
        
        Args:
            lstm_input: (lookback, features) - LSTM 입력
            xgboost_input: (features,) - XGBoost 입력
            stock_code: 무시됨 (동기 버전에서는 감성분석 제외)
        
        Returns:
            score: 최종 예측 점수 (0-1)
        """
        scores = {}
        weights = {}
        
        # 1. LSTM 예측
        if self.lstm_loaded:
            try:
                lstm_score = self.lstm_model.predict(lstm_input)[0]
                scores['lstm'] = lstm_score
                weights['lstm'] = self.lstm_weight
            except:
                pass
        
        # 2. XGBoost 예측
        if self.xgboost_loaded:
            try:
                xgboost_score = self.xgboost_model.predict(xgboost_input)[0]
                scores['xgboost'] = xgboost_score
                weights['xgboost'] = self.xgboost_weight
            except:
                pass
        
        # 가중 평균
        total_weight = sum(weights.values())
        if total_weight == 0:
            return 0.5
        
        final_score = sum(
            scores[model] * (weight / total_weight)
            for model, weight in weights.items()
        )
        
        return final_score
    
    def is_ready(self):
        """모델이 예측 가능한 상태인지 확인"""
        return self.lstm_loaded or self.xgboost_loaded
