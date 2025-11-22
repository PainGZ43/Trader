"""
LSTM Model for Stock Price Prediction
시계열 데이터를 기반으로 한 LSTM 딥러닝 모델
"""
import numpy as np

# TensorFlow는 선택사항 (Python 3.11 호환 문제)
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
    TENSORFLOW_AVAILABLE = True
except Exception:
    TENSORFLOW_AVAILABLE = False
    print("[WARNING] TensorFlow not available. AI features will be limited to XGBoost.")

from sklearn.model_selection import train_test_split
from logger import logger
import os

class LSTMPredictor:
    """LSTM 기반 주가 예측 모델"""
    
    def __init__(self, lookback=100, n_features=22, model_path='models/lstm_model.h5'):
        self.lookback = lookback
        self.n_features = n_features
        self.model_path = model_path
        self.model = None
        
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
    
    def build_model(self):
        """LSTM 모델 구축"""
        if not TENSORFLOW_AVAILABLE:
            logger.warning("TensorFlow not available, cannot build model")
            return None
        
        logger.info("Building LSTM model...")
        
        model = Sequential([
            # LSTM Layer 1
            LSTM(128, return_sequences=True, input_shape=(self.lookback, self.n_features)),
            Dropout(0.2),
            
            # LSTM Layer 2
            LSTM(64, return_sequences=False),
            Dropout(0.2),
            
            # Dense Layers
            Dense(32, activation='relu'),
            Dropout(0.1),
            
            # Output Layer
            Dense(1, activation='sigmoid')
        ])
        
        # Compile
        model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy', 'AUC']
        )
        
        self.model = model
        logger.info("Model built successfully")
        logger.info(f"Total parameters: {model.count_params():,}")
        
        return model
    
    def train(self, X, y, validation_split=0.2, epochs=50, batch_size=64):
        """
        모델 학습
        
        Args:
            X: (samples, lookback, features)
            y: (samples,) - binary labels
            validation_split: 검증 데이터 비율
            epochs: 학습 에포크 수
            batch_size: 배치 크기
        
        Returns:
            history: 학습 기록
        """
        if self.model is None:
            if not TENSORFLOW_AVAILABLE:
                logger.warning("TensorFlow not available, cannot train model")
                return None
            self.build_model()

        
        logger.info(f"Training LSTM model... (epochs={epochs}, batch_size={batch_size})")
        
        # Callbacks
        early_stop = EarlyStopping(
            monitor='val_loss',
            patience=10,
            restore_best_weights=True,
            verbose=1
        )
        
        checkpoint = ModelCheckpoint(
            self.model_path,
            monitor='val_accuracy',
            save_best_only=True,
            verbose=1
        )
        
        # Train
        history = self.model.fit(
            X, y,
            validation_split=validation_split,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=[early_stop, checkpoint],
            verbose=1
        )
        
        # Evaluate
        val_loss, val_acc, val_auc = self.model.evaluate(
            X[-int(len(X)*validation_split):], 
            y[-int(len(y)*validation_split):],
            verbose=0
        )
        
        logger.info(f"Training completed!")
        logger.info(f"Validation - Loss: {val_loss:.4f}, Accuracy: {val_acc:.4f}, AUC: {val_auc:.4f}")
        
        return history
    
    def predict(self, X):
        """
        예측 수행
        
        Args:
            X: (samples, lookback, features) or (lookback, features) for single prediction
        
        Returns:
            predictions: 상승 확률 (0-1)
        """
        if self.model is None:
            if not TENSORFLOW_AVAILABLE:
                return np.zeros(len(X)) if X.ndim > 1 else np.array([0.5])
            logger.warning("Model not loaded. Loading from disk...")
            self.load_model()

        
        # Single sample handling
        if X.ndim == 2:
            X = np.expand_dims(X, axis=0)
        
        predictions = self.model.predict(X, verbose=0)
        return predictions.flatten()
    
    def save_model(self, path=None):
        """모델 저장"""
        if path is None:
            path = self.model_path
        
        self.model.save(path)
        logger.info(f"Model saved to {path}")
    
    def load_model(self, path=None):
        """모델 로드"""
        if not TENSORFLOW_AVAILABLE:
            return False
            
        if path is None:
            path = self.model_path
        
        if not os.path.exists(path):
            logger.warning(f"Model file not found: {path}")
            logger.info("Building new model instead...")
            self.build_model()
            return False
        
        try:
            self.model = load_model(path)
            logger.info(f"Model loaded from {path}")
            return True
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            logger.info("Building new model instead...")
            self.build_model()
            return False
    
    def evaluate(self, X_test, y_test):
        """
        모델 평가
        
        Returns:
            dict with metrics
        """
        if self.model is None:
            self.load_model()
        
        loss, accuracy, auc = self.model.evaluate(X_test, y_test, verbose=0)
        
        # Confusion Matrix
        y_pred = (self.predict(X_test) > 0.5).astype(int)
        
        from sklearn.metrics import classification_report, confusion_matrix
        
        logger.info("Model Evaluation:")
        logger.info(f"Loss: {loss:.4f}")
        logger.info(f"Accuracy: {accuracy:.4f}")
        logger.info(f"AUC: {auc:.4f}")
        logger.info("\nClassification Report:")
        logger.info(classification_report(y_test, y_pred))
        
        return {
            'loss': loss,
            'accuracy': accuracy,
            'auc': auc,
            'confusion_matrix': confusion_matrix(y_test, y_pred)
        }
