"""
XGBoost Model for Stock Price Prediction
기술적 지표 기반 XGBo

ost 분류 모델
"""
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, accuracy_score, roc_auc_score
from logger import logger
import joblib
import os

class XGBoostPredictor:
    """XGBoost 기반 주가 예측 모델"""
    
    def __init__(self, model_path='models/xgboost_model.pkl'):
        self.model_path = model_path
        self.model = None
        self.feature_importance = None
        
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
    
    def build_model(self):
        """XGBoost 모델 구축"""
        logger.info("Building XGBoost model...")
        
        self.model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            gamma=0.1,
            reg_alpha=0.1,
            reg_lambda=1,
            random_state=42,
            use_label_encoder=False,
            eval_metric='logloss',
            n_jobs=1,  # Prevent OpenMP crash in PyQt thread
            early_stopping_rounds=20 # Moved here for newer XGBoost versions
        )
        
        logger.info("XGBoost model built successfully")
        return self.model
    
    def train(self, X, y, validation_split=0.2):
        """
        모델 학습
        
        Args:
            X: (samples, features) - 기술적 지표
            y: (samples,) - binary labels
            validation_split: 검증 데이터 비율
        
        Returns:
            metrics: 평가 지표
        """
        if self.model is None:
            self.build_model()
        
        logger.info(f"Training XGBoost model with {X.shape[0]} samples...")
        
        # Train/Validation split
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=validation_split, random_state=42, stratify=y
        )
        
        # Train with early stopping
        eval_set = [(X_train, y_train), (X_val, y_val)]
        
        try:
            self.model.fit(
                X_train, y_train,
                eval_set=eval_set,
                verbose=False # Reduce console spam
            )
        except Exception as e:
            logger.error(f"XGBoost training failed: {e}")
            return {'accuracy': 0, 'auc': 0, 'feature_importance': None}
        
        # Evaluate
        y_pred = self.model.predict(X_val)
        y_pred_proba = self.model.predict_proba(X_val)[:, 1]
        
        accuracy = accuracy_score(y_val, y_pred)
        auc = roc_auc_score(y_val, y_pred_proba)
        
        logger.info(f"Training completed!")
        logger.info(f"Validation Accuracy: {accuracy:.4f}")
        logger.info(f"Validation AUC: {auc:.4f}")
        
        # Feature Importance
        self.feature_importance = self.model.feature_importances_
        
        # Save model
        self.save_model()
        
        return {
            'accuracy': accuracy,
            'auc': auc,
            'feature_importance': self.feature_importance
        }
    
    def predict(self, X):
        """
        예측 수행
        
        Args:
            X: (samples, features) or (features,) for single prediction
        
        Returns:
            predictions: 상승 확률 (0-1)
        """
        if self.model is None:
            logger.warning("Model not loaded. Loading from disk...")
            self.load_model()
        
        # Single sample handling
        if X.ndim == 1:
            X = X.reshape(1, -1)
        
        predictions = self.model.predict_proba(X)[:, 1]
        return predictions
    
    def save_model(self, path=None):
        """모델 저장"""
        if path is None:
            path = self.model_path
        
        joblib.dump(self.model, path)
        logger.info(f"Model saved to {path}")
    
    def load_model(self, path=None):
        """모델 로드"""
        if path is None:
            path = self.model_path
        
        if not os.path.exists(path):
            logger.warning(f"Model file not found: {path}")
            logger.info("Building new model instead...")
            self.build_model()
            return False
        
        try:
            self.model = joblib.load(path)
            logger.info(f"Model loaded from {path}")
            return True
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            logger.info("Building new model instead...")
            self.build_model()
            return False
    
    def get_feature_importance(self, feature_names=None):
        """
        Feature Importance 반환
        
        Args:
            feature_names: 특징 이름 리스트
        
        Returns:
            dict or None
        """
        if self.feature_importance is None:
            if self.model is not None:
                self.feature_importance = self.model.feature_importances_
            else:
                return None
        
        if feature_names is None:
            from ai.indicators import IndicatorCalculator
            feature_names = IndicatorCalculator.get_feature_names()
        
        importance_dict = dict(zip(feature_names, self.feature_importance))
        
        # 중요도 순으로 정렬
        sorted_importance = sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)
        
        logger.info("Feature Importance (Top 10):")
        for name, importance in sorted_importance[:10]:
            logger.info(f"  {name}: {importance:.4f}")
        
        return dict(sorted_importance)
