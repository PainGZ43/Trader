# Phase 4: AI 모델 개발 상세 계획

**목표**: 딥러닝 기반 가격 예측 모델 구축

**예상 기간**: 5-7일

---

## 1. AI 모델 아키텍처 설계

### 1.1 모델 정의

#### [NEW] [ai/model.py](file:///e:/GitHub/UpbitTrader/ai/model.py)

**주요 기능**:

#### 1.1.1 LSTM 모델

```python
import tensorflow as tf
from tensorflow import keras
from keras.models import Sequential
from keras.layers import LSTM, GRU, Dense, Dropout, BatchNormalization
from keras.optimizers import Adam
from keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau

class PricePredictor Model:
    """가격 예측 LSTM 모델"""
    
    def __init__(self, input_shape, model_type='lstm'):
        """
        Args:
            input_shape: (time_steps, features)
            model_type: 'lstm' or 'gru'
        """
        self.input_shape = input_shape
        self.model_type = model_type
        self.model = None
        
    def build_model(self, lstm_units=[128, 64, 32], dropout_rate=0.2):
        """모델 구축"""
        model = Sequential()
        
        # 첫 번째 LSTM/GRU 레이어
        if self.model_type == 'lstm':
            model.add(LSTM(
                units=lstm_units[0],
                return_sequences=True,
                input_shape=self.input_shape
            ))
        else:
            model.add(GRU(
                units=lstm_units[0],
                return_sequences=True,
                input_shape=self.input_shape
            ))
        
        model.add(Dropout(dropout_rate))
        model.add(BatchNormalization())
        
        # 중간 레이어들
        for units in lstm_units[1:-1]:
            if self.model_type == 'lstm':
                model.add(LSTM(units=units, return_sequences=True))
            else:
                model.add(GRU(units=units, return_sequences=True))
            
            model.add(Dropout(dropout_rate))
            model.add(BatchNormalization())
        
        # 마지막 LSTM/GRU 레이어
        if self.model_type == 'lstm':
            model.add(LSTM(units=lstm_units[-1]))
        else:
            model.add(GRU(units=lstm_units[-1]))
        
        model.add(Dropout(dropout_rate))
        model.add(BatchNormalization())
        
        # 출력 레이어
        model.add(Dense(units=32, activation='relu'))
        model.add(Dense(units=16, activation='relu'))
        model.add(Dense(units=1))  # 가격 예측
        
        # 컴파일
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae', 'mape']
        )
        
        self.model = model
        return model
    
    def summary(self):
        """모델 요약"""
        if self.model:
            return self.model.summary()
```

#### 1.1.2 멀티태스크 모델 (가격 + 방향)

```python
class MultiTaskModel:
    """가격 예측 + 방향 예측 모델"""
    
    def __init__(self, input_shape):
        self.input_shape = input_shape
        self.model = None
    
    def build_model(self):
        """멀티태스크 모델 구축"""
        from keras.layers import Input
        from keras.models import Model
        
        # 입력
        inputs = Input(shape=self.input_shape)
        
        # 공유 레이어
        x = LSTM(128, return_sequences=True)(inputs)
        x = Dropout(0.2)(x)
        x = LSTM(64)(x)
        x = Dropout(0.2)(x)
        
        # 가격 예측 브랜치
        price_branch = Dense(32, activation='relu')(x)
        price_output = Dense(1, name='price')(price_branch)
        
        # 방향 예측 브랜치 (상승/하락/보합)
        direction_branch = Dense(32, activation='relu')(x)
        direction_output = Dense(3, activation='softmax', name='direction')(direction_branch)
        
        # 모델 생성
        model = Model(inputs=inputs, outputs=[price_output, direction_output])
        
        # 컴파일
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss={
                'price': 'mse',
                'direction': 'categorical_crossentropy'
            },
            loss_weights={
                'price': 0.7,
                'direction': 0.3
            },
            metrics={
                'price': ['mae'],
                'direction': ['accuracy']
            }
        )
        
        self.model = model
        return model
```

---

## 2. 데이터 준비

### 2.1 학습 데이터 생성

#### [NEW] [ai/data_generator.py](file:///e:/GitHub/UpbitTrader/ai/data_generator.py)

```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

class TrainingDataGenerator:
    """학습 데이터 생성 클래스"""
    
    def __init__(self, lookback=60, forecast_horizon=1):
        """
        Args:
            lookback: 과거 몇 개의 데이터를 볼지 (time steps)
            forecast_horizon: 미래 몇 스텝 예측할지
        """
        self.lookback = lookback
        self.forecast_horizon = forecast_horizon
    
    def create_sequences(self, data, target_column='close'):
        """시계열 시퀀스 생성
        
        Returns:
            X: (samples, lookback, features)
            y: (samples,)
        """
        X, y = [], []
        
        for i in range(len(data) - self.lookback - self.forecast_horizon + 1):
            # 입력: 과거 lookback개의 데이터
            X.append(data[i:i + self.lookback])
            
            # 타겟: forecast_horizon 후의 가격
            y.append(data[i + self.lookback + self.forecast_horizon - 1][target_column])
        
        return np.array(X), np.array(y)
    
    def prepare_training_data(self, df, feature_columns, target_column='close', 
                            test_size=0.2, validation_size=0.1):
        """학습 데이터 준비"""
        
        # 피처 선택
        data = df[feature_columns].values
        
        # 시퀀스 생성
        X, y = self.create_sequences(data, target_column)
        
        # Train/Val/Test 분할
        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y, test_size=test_size, shuffle=False
        )
        
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp, test_size=validation_size, shuffle=False
        )
        
        print(f"📊 데이터 형태:")
        print(f"  Train: X={X_train.shape}, y={y_train.shape}")
        print(f"  Val:   X={X_val.shape}, y={y_val.shape}")
        print(f"  Test:  X={X_test.shape}, y={y_test.shape}")
        
        return {
            'X_train': X_train, 'y_train': y_train,
            'X_val': X_val, 'y_val': y_val,
            'X_test': X_test, 'y_test': y_test
        }
    
    def create_direction_labels(self, prices, threshold=0.001):
        """방향 레이블 생성 (0: 하락, 1: 보합, 2: 상승)"""
        changes = (prices - np.roll(prices, 1)) / np.roll(prices, 1)
        
        labels = np.zeros(len(changes))
        labels[changes > threshold] = 2  # 상승
        labels[changes < -threshold] = 0  # 하락
        labels[(changes >= -threshold) & (changes <= threshold)] = 1  # 보합
        
        # One-hot encoding
        from keras.utils import to_categorical
        return to_categorical(labels, num_classes=3)
```

---

## 3. 모델 학습

### 3.1 학습 파이프라인

#### [NEW] [ai/trainer.py](file:///e:/GitHub/UpbitTrader/ai/trainer.py)

```python
import os
from datetime import datetime
import matplotlib.pyplot as plt
from keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau, TensorBoard

class ModelTrainer:
    """모델 학습 클래스"""
    
    def __init__(self, model, model_name='price_predictor'):
        self.model = model
        self.model_name = model_name
        self.history = None
        
    def train(self, X_train, y_train, X_val, y_val, 
              epochs=100, batch_size=32, patience=10):
        """모델 학습"""
        
        # 콜백 설정
        callbacks = self._get_callbacks(patience)
        
        print(f"🤖 모델 학습 시작...")
        print(f"  Epochs: {epochs}")
        print(f"  Batch size: {batch_size}")
        
        # 학습
        self.history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=1
        )
        
        print("✅ 학습 완료")
        
        return self.history
    
    def _get_callbacks(self, patience):
        """콜백 함수들"""
        
        # 모델 저장 경로
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        model_dir = f'./models/{self.model_name}'
        os.makedirs(model_dir, exist_ok=True)
        
        model_path = os.path.join(model_dir, f'best_model_{timestamp}.h5')
        
        callbacks = [
            # 조기 종료
            EarlyStopping(
                monitor='val_loss',
                patience=patience,
                restore_best_weights=True,
                verbose=1
            ),
            
            # 최적 모델 저장
            ModelCheckpoint(
                filepath=model_path,
                monitor='val_loss',
                save_best_only=True,
                verbose=1
            ),
            
            # 학습률 감소
            ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=1e-7,
                verbose=1
            ),
            
            # TensorBoard
            TensorBoard(
                log_dir=f'./logs/{self.model_name}/{timestamp}',
                histogram_freq=1
            )
        ]
        
        return callbacks
    
    def plot_training_history(self, save_path=None):
        """학습 이력 시각화"""
        if self.history is None:
            print("학습 이력이 없습니다.")
            return
        
        fig, axes = plt.subplots(1, 2, figsize=(15, 5))
        
        # Loss
        axes[0].plot(self.history.history['loss'], label='Train Loss')
        axes[0].plot(self.history.history['val_loss'], label='Val Loss')
        axes[0].set_title('Model Loss')
        axes[0].set_xlabel('Epoch')
        axes[0].set_ylabel('Loss')
        axes[0].legend()
        axes[0].grid(True)
        
        # MAE
        axes[1].plot(self.history.history['mae'], label='Train MAE')
        axes[1].plot(self.history.history['val_mae'], label='Val MAE')
        axes[1].set_title('Model MAE')
        axes[1].set_xlabel('Epoch')
        axes[1].set_ylabel('MAE')
        axes[1].legend()
        axes[1].grid(True)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path)
        else:
            plt.show()
    
    def evaluate(self, X_test, y_test):
        """모델 평가"""
        print("\n📊 모델 평가:")
        results = self.model.evaluate(X_test, y_test, verbose=0)
        
        print(f"  Test Loss: {results[0]:.6f}")
        print(f"  Test MAE: {results[1]:.6f}")
        print(f"  Test MAPE: {results[2]:.2f}%")
        
        return results
```

---

## 4. 예측 서비스

### 4.1 실시간 예측

#### [NEW] [ai/predictor.py](file:///e:/GitHub/UpbitTrader/ai/predictor.py)

```python
import numpy as np
from keras.models import load_model

class PricePredictor:
    """가격 예측 서비스"""
    
    def __init__(self, model_path=None):
        self.model = None
        self.scaler = None
        
        if model_path:
            self.load_model(model_path)
    
    def load_model(self, model_path):
        """모델 로드"""
        try:
            self.model = load_model(model_path)
            print(f"✅ 모델 로드 성공: {model_path}")
        except Exception as e:
            print(f"❌ 모델 로드 실패: {e}")
    
    def predict(self, data):
        """예측 수행
        
        Args:
            data: (lookback, features) 형태의 입력 데이터
        
        Returns:
            predicted_price: 예측 가격
        """
        if self.model is None:
            raise ValueError("모델이 로드되지 않았습니다.")
        
        # 입력 형태 조정 (batch 차원 추가)
        if len(data.shape) == 2:
            data = np.expand_dims(data, axis=0)
        
        # 예측
        prediction = self.model.predict(data, verbose=0)
        
        return prediction[0][0]
    
    def predict_with_confidence(self, data, n_predictions=10):
        """신뢰도와 함께 예측
        
        여러 번 예측하여 평균과 표준편차 계산
        """
        predictions = []
        
        for _ in range(n_predictions):
            pred = self.predict(data)
            predictions.append(pred)
        
        mean_pred = np.mean(predictions)
        std_pred = np.std(predictions)
        confidence = 1 - (std_pred / mean_pred)  # 간단한 신뢰도 계산
        
        return {
            'predicted_price': mean_pred,
            'std': std_pred,
            'confidence': max(0, min(1, confidence))  # 0-1 범위로 제한
        }
    
    def generate_signal(self, current_price, predicted_price, threshold=0.02):
        """매매 시그널 생성
        
        Args:
            current_price: 현재 가격
            predicted_price: 예측 가격
            threshold: 시그널 발생 임계값 (2%)
        
        Returns:
            signal: 'buy', 'sell', 'hold'
            change_percent: 예상 변화율
        """
        change_percent = (predicted_price - current_price) / current_price
        
        if change_percent > threshold:
            signal = 'buy'
        elif change_percent < -threshold:
            signal = 'sell'
        else:
            signal = 'hold'
        
        return {
            'signal': signal,
            'change_percent': change_percent * 100,
            'current_price': current_price,
            'predicted_price': predicted_price
        }
```

---

## 5. 모델 평가 및 검증

### 5.1 성능 평가

#### [NEW] [ai/evaluator.py](file:///e:/GitHub/UpbitTrader/ai/evaluator.py)

```python
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

class ModelEvaluator:
    """모델 평가 클래스"""
    
    @staticmethod
    def calculate_metrics(y_true, y_pred):
        """평가 지표 계산"""
        mse = mean_squared_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_true, y_pred)
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
        r2 = r2_score(y_true, y_pred)
        
        return {
            'MSE': mse,
            'RMSE': rmse,
            'MAE': mae,
            'MAPE': mape,
            'R2': r2
        }
    
    @staticmethod
    def plot_predictions(y_true, y_pred, title='Predictions vs Actual'):
        """예측 결과 시각화"""
        fig, axes = plt.subplots(2, 1, figsize=(15, 10))
        
        # 시계열 비교
        axes[0].plot(y_true, label='Actual', alpha=0.7)
        axes[0].plot(y_pred, label='Predicted', alpha=0.7)
        axes[0].set_title(title)
        axes[0].set_xlabel('Time')
        axes[0].set_ylabel('Price')
        axes[0].legend()
        axes[0].grid(True)
        
        # 산점도
        axes[1].scatter(y_true, y_pred, alpha=0.5)
        axes[1].plot([y_true.min(), y_true.max()], 
                     [y_true.min(), y_true.max()], 
                     'r--', lw=2)
        axes[1].set_title('Scatter Plot')
        axes[1].set_xlabel('Actual Price')
        axes[1].set_ylabel('Predicted Price')
        axes[1].grid(True)
        
        plt.tight_layout()
        plt.show()
    
    @staticmethod
    def calculate_directional_accuracy(y_true, y_pred):
        """방향 정확도 계산"""
        true_direction = np.sign(np.diff(y_true))
        pred_direction = np.sign(np.diff(y_pred))
        
        accuracy = np.mean(true_direction == pred_direction) * 100
        
        return accuracy
```

---

## 6. 자동 재학습

### 6.1 재학습 스케줄러

#### [NEW] [ai/retraining_scheduler.py](file:///e:/GitHub/UpbitTrader/ai/retraining_scheduler.py)

```python
import schedule
import time
from datetime import datetime

class RetrainingScheduler:
    """모델 자동 재학습 스케줄러"""
    
    def __init__(self, trainer, data_pipeline, market='KRW-BTC'):
        self.trainer = trainer
        self.data_pipeline = data_pipeline
        self.market = market
    
    def retrain_model(self):
        """모델 재학습 실행"""
        print(f"\n{'='*50}")
        print(f"🔄 모델 재학습 시작: {datetime.now()}")
        print(f"{'='*50}\n")
        
        # 1. 최신 데이터 수집
        df = self.data_pipeline.get_processed_data(self.market, days=90, use_cache=False)
        
        # 2. 학습 데이터 준비
        # ... (데이터 준비 로직)
        
        # 3. 모델 학습
        # ... (학습 로직)
        
        # 4. 평가
        # ... (평가 로직)
        
        print(f"\n✅ 재학습 완료: {datetime.now()}\n")
    
    def schedule_weekly_retraining(self, day='sunday', time='02:00'):
        """주간 재학습 스케줄"""
        schedule.every().sunday.at(time).do(self.retrain_model)
        
        print(f"📅 주간 재학습 스케줄 설정: 매주 {day} {time}")
        
        while True:
            schedule.run_pending()
            time.sleep(3600)  # 1시간마다 체크
    
    def schedule_daily_retraining(self, time='02:00'):
        """일일 재학습 스케줄"""
        schedule.every().day.at(time).do(self.retrain_model)
        
        print(f"📅 일일 재학습 스케줄 설정: 매일 {time}")
        
        while True:
            schedule.run_pending()
            time.sleep(3600)
```

---

## 검증 체크리스트

### ✅ 모델 구축
- [ ] LSTM 모델 정의
- [ ] GRU 모델 정의
- [ ] 멀티태스크 모델 정의
- [ ] 하이퍼파라미터 설정

### ✅ 데이터 준비
- [ ] 시계열 시퀀스 생성
- [ ] Train/Val/Test 분할
- [ ] 정규화/표준화
- [ ] 피처 선택

### ✅ 학습
- [ ] 모델 학습 실행
- [ ] 조기 종료 동작 확인
- [ ] 최적 모델 저장
- [ ] 학습 이력 시각화

### ✅ 평가
- [ ] MSE, MAE, MAPE 계산
- [ ] 방향 정확도 계산
- [ ] 예측 결과 시각화
- [ ] R2 스코어 확인

### ✅ 예측
- [ ] 실시간 예측 테스트
- [ ] 신뢰도 계산
- [ ] 시그널 생성
- [ ] 모델 로드/저장

---

## 다음 단계

Phase 4 완료 후:
- ✅ Phase 5: 트레이딩 로직 구현
- 💼 AI 신호 기반 주문 실행
- 🎯 리스크 관리 통합

> [!IMPORTANT]
> AI 모델의 예측은 참고용입니다. 실제 수익을 보장하지 않으며, 충분한 백테스팅과 검증이 필요합니다.

> [!TIP]
> 모델의 성능을 높이려면 다양한 피처를 추가하고, 하이퍼파라미터 튜닝을 진행하세요. AutoML 도구 활용도 고려해보세요.
