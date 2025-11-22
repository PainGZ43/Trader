# Phase 3: 데이터 수집 및 처리 상세 계획

**목표**: 시장 데이터 수집 자동화 및 기술적 지표 계산

**예상 기간**: 4-5일

---

## 1. 시장 데이터 수집

###1.1 데이터 수집 모듈

#### [NEW] [data/market_data.py](file:///e:/GitHub/UpbitTrader/data/market_data.py)

**주요 기능**:

#### 1.1.1 OHLCV 데이터 수집

```python
import pandas as pd
from datetime import datetime, timedelta
from api.upbit_api import UpbitAPI
from database.db_manager import DatabaseManager

class MarketDataCollector:
    """시장 데이터 수집 클래스"""
    
    def __init__(self, api: UpbitAPI, db: DatabaseManager):
        self.api = api
        self.db = db
        
    def collect_historical_data(self, market, days=30, interval='1min'):
        """과거 데이터 수집
        
        Args:
            market: 마켓 코드 (예: KRW-BTC)
            days: 수집할 일수
            interval: 간격 (1min, 5min, 15min, 30min, 1hour, 1day)
        """
        print(f"📊 {market} 데이터 수집 시작 ({days}일, {interval})")
        
        all_candles = []
        
        if interval.endswith('min'):
            unit = int(interval.replace('min', ''))
            total_requests = (days * 24 * 60) // (unit * 200) + 1
            
            for i in range(total_requests):
                candles = self.api.get_candles_minutes(market, unit=unit, count=200)
                all_candles.extend(candles)
                
                if len(candles) < 200:
                    break
                    
        elif interval == '1hour':
            total_requests = (days * 24) // 200 + 1
            for i in range(total_requests):
                candles = self.api.get_candles_minutes(market, unit=240, count=200)
                all_candles.extend(candles)
                
        elif interval == '1day':
            candles = self.api.get_candles_days(market, count=days)
            all_candles.extend(candles)
        
        # DataFrame 변환
        df = self._candles_to_dataframe(all_candles)
        
        # 데이터베이스 저장
        self._save_to_database(market, df)
        
        print(f"✅ {len(df)}개 캔들 수집 완료")
        return df
    
    def collect_realtime_data(self, market):
        """실시간 데이터 수집 (최신 1개)"""
        candles = self.api.get_candles_minutes(market, unit=1, count=1)
        return self._candles_to_dataframe(candles)
    
    def _candles_to_dataframe(self, candles):
        """캔들 데이터를 DataFrame으로 변환"""
        df = pd.DataFrame(candles)
        
        if df.empty:
            return df
        
        df['timestamp'] = pd.to_datetime(df['candle_date_time_kst'])
        df = df.rename(columns={
            'opening_price': 'open',
            'high_price': 'high',
            'low_price': 'low',
            'trade_price': 'close',
            'candle_acc_trade_volume': 'volume',
            'candle_acc_trade_price': 'value'
        })
        
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume', 'value']]
        df = df.sort_values('timestamp').reset_index(drop=True)
        df = df.drop_duplicates(subset=['timestamp'])
        
        return df
    
    def _save_to_database(self, market, df):
        """데이터베이스에 저장"""
        for _, row in df.iterrows():
            self.db.insert_market_data(
                market=market,
                timestamp=row['timestamp'],
                ohlcv={
                    'open': row['open'],
                    'high': row['high'],
                    'low': row['low'],
                    'close': row['close'],
                    'volume': row['volume'],
                    'value': row['value']
                }
            )
```

#### 1.1.2 데이터 업데이트

```python
def update_market_data(self, market, interval='1min'):
    """데이터 업데이트 (마지막 저장된 시간 이후)"""
    last_timestamp = self.db.get_last_timestamp(market)
    
    if last_timestamp is None:
        # 처음 수집
        return self.collect_historical_data(market, days=30, interval=interval)
    
    # 마지막 시간 이후 데이터만 수집
    print(f"🔄 {market} 데이터 업데이트 (마지막: {last_timestamp})")
    
    now = datetime.now()
    time_diff = (now - last_timestamp).total_seconds()
    
    if interval == '1min':
        count = min(int(time_diff / 60) + 1, 200)
        candles = self.api.get_candles_minutes(market, unit=1, count=count)
    
    df = self._candles_to_dataframe(candles)
    
    # 새로운 데이터만 저장
    df = df[df['timestamp'] > last_timestamp]
    
    if not df.empty:
        self._save_to_database(market, df)
        print(f"✅ {len(df)}개 새로운 캔들 추가")
    
    return df
```

#### 1.1.3 다중 마켓 수집

```python
def collect_multiple_markets(self, markets, days=30, interval='1min'):
    """여러 마켓 동시 수집"""
    results = {}
    
    for market in markets:
        try:
            df = self.collect_historical_data(market, days, interval)
            results[market] = df
            time.sleep(0.1)  # Rate limiting
        except Exception as e:
            print(f"❌ {market} 수집 실패: {e}")
            results[market] = None
    
    return results
```

---

## 2. 기술적 지표 계산

### 2.1 지표 계산 모듈

#### [NEW] [data/indicators.py](file:///e:/GitHub/UpbitTrader/data/indicators.py)

**주요 기능**:

#### 2.1.1 이동평균 (MA)

```python
import pandas as pd
import numpy as np

class TechnicalIndicators:
    """기술적 지표 계산 클래스"""
    
    @staticmethod
    def calculate_sma(df, period=20, column='close'):
        """단순 이동평균 (SMA)"""
        return df[column].rolling(window=period).mean()
    
    @staticmethod
    def calculate_ema(df, period=20, column='close'):
        """지수 이동평균 (EMA)"""
        return df[column].ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def calculate_wma(df, period=20, column='close'):
        """가중 이동평균 (WMA)"""
        weights = np.arange(1, period + 1)
        return df[column].rolling(window=period).apply(
            lambda x: np.dot(x, weights) / weights.sum(), raw=True
        )
```

#### 2.1.2 RSI (Relative Strength Index)

```python
@staticmethod
def calculate_rsi(df, period=14, column='close'):
    """RSI 계산"""
    delta = df[column].diff()
    
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi
```

#### 2.1.3 MACD (Moving Average Convergence Divergence)

```python
@staticmethod
def calculate_macd(df, fast=12, slow=26, signal=9, column='close'):
    """MACD 계산"""
    ema_fast = df[column].ewm(span=fast, adjust=False).mean()
    ema_slow = df[column].ewm(span=slow, adjust=False).mean()
    
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    histogram = macd - signal_line
    
    return pd.DataFrame({
        'macd': macd,
        'signal': signal_line,
        'histogram': histogram
    })
```

#### 2.1.4 볼린저 밴드 (Bollinger Bands)

```python
@staticmethod
def calculate_bollinger_bands(df, period=20, std_dev=2, column='close'):
    """볼린저 밴드 계산"""
    sma = df[column].rolling(window=period).mean()
    std = df[column].rolling(window=period).std()
    
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    
    return pd.DataFrame({
        'bb_upper': upper_band,
        'bb_middle': sma,
        'bb_lower': lower_band
    })
```

#### 2.1.5 스토캐스틱 (Stochastic Oscillator)

```python
@staticmethod
def calculate_stochastic(df, period=14, k_period=3, d_period=3):
    """스토캐스틱 계산"""
    low_min = df['low'].rolling(window=period).min()
    high_max = df['high'].rolling(window=period).max()
    
    k = 100 * ((df['close'] - low_min) / (high_max - low_min))
    k = k.rolling(window=k_period).mean()  # %K
    d = k.rolling(window=d_period).mean()  # %D
    
    return pd.DataFrame({
        'stoch_k': k,
        'stoch_d': d
    })
```

#### 2.1.6 ATR (Average True Range)

```python
@staticmethod
def calculate_atr(df, period=14):
    """ATR 계산 (변동성 지표)"""
    high_low = df['high'] - df['low']
    high_close = abs(df['high'] - df['close'].shift())
    low_close = abs(df['low'] - df['close'].shift())
    
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.rolling(window=period).mean()
    
    return atr
```

#### 2.1.7 OBV (On Balance Volume)

```python
@staticmethod
def calculate_obv(df):
    """OBV 계산 (거래량 지표)"""
    obv = (np.sign(df['close'].diff()) * df['volume']).fillna(0).cumsum()
    return obv
```

#### 2.1.8 ADX (Average Directional Index)

```python
@staticmethod
def calculate_adx(df, period=14):
    """ADX 계산 (추세 강도)"""
    high_diff = df['high'].diff()
    low_diff = -df['low'].diff()
    
    plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
    minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)
    
    tr = TechnicalIndicators.calculate_atr(df, period=1)
    
    plus_di = 100 * (plus_dm.rolling(window=period).mean() / tr.rolling(window=period).mean())
    minus_di = 100 * (minus_dm.rolling(window=period).mean() / tr.rolling(window=period).mean())
    
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(window=period).mean()
    
    return pd.DataFrame({
        'adx': adx,
        'plus_di': plus_di,
        'minus_di': minus_di
    })
```

### 2.2 통합 지표 계산

```python
class IndicatorCalculator:
    """지표 통합 계산 클래스"""
    
    def __init__(self):
        self.indicators = TechnicalIndicators()
    
    def calculate_all_indicators(self, df):
        """모든 지표 계산"""
        result = df.copy()
        
        # 이동평균
        result['sma_5'] = self.indicators.calculate_sma(df, period=5)
        result['sma_20'] = self.indicators.calculate_sma(df, period=20)
        result['sma_60'] = self.indicators.calculate_sma(df, period=60)
        result['ema_12'] = self.indicators.calculate_ema(df, period=12)
        result['ema_26'] = self.indicators.calculate_ema(df, period=26)
        
        # RSI
        result['rsi'] = self.indicators.calculate_rsi(df, period=14)
        
        # MACD
        macd_df = self.indicators.calculate_macd(df)
        result = pd.concat([result, macd_df], axis=1)
        
        # 볼린저 밴드
        bb_df = self.indicators.calculate_bollinger_bands(df)
        result = pd.concat([result, bb_df], axis=1)
        
        # 스토캐스틱
        stoch_df = self.indicators.calculate_stochastic(df)
        result = pd.concat([result, stoch_df], axis=1)
        
        # ATR
        result['atr'] = self.indicators.calculate_atr(df)
        
        # OBV
        result['obv'] = self.indicators.calculate_obv(df)
        
        # ADX
        adx_df = self.indicators.calculate_adx(df)
        result = pd.concat([result, adx_df], axis=1)
        
        return result
```

---

## 3. 데이터 전처리

### 3.1 전처리 모듈

#### [NEW] [data/preprocessor.py](file:///e:/GitHub/UpbitTrader/data/preprocessor.py)

```python
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler, StandardScaler

class DataPreprocessor:
    """데이터 전처리 클래스"""
    
    def __init__(self):
        self.scaler = MinMaxScaler()
    
    def remove_outliers(self, df, column='close', threshold=3):
        """이상치 제거 (Z-score 방법)"""
        mean = df[column].mean()
        std = df[column].std()
        z_scores = np.abs((df[column] - mean) / std)
        
        return df[z_scores < threshold].copy()
    
    def fill_missing_values(self, df, method='ffill'):
        """결측치 처리
        
        Args:
            method: 'ffill' (forward fill), 'bfill' (backward fill), 'interpolate'
        """
        if method == 'interpolate':
            return df.interpolate(method='linear')
        else:
            return df.fillna(method=method)
    
    def normalize_data(self, df, columns=None):
        """데이터 정규화 (0-1 범위)"""
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        df_normalized = df.copy()
        df_normalized[columns] = self.scaler.fit_transform(df[columns])
        
        return df_normalized
    
    def standardize_data(self, df, columns=None):
        """데이터 표준화 (평균 0, 표준편차 1)"""
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        scaler = StandardScaler()
        df_standardized = df.copy()
        df_standardized[columns] = scaler.fit_transform(df[columns])
        
        return df_standardized
    
    def create_time_features(self, df):
        """시간 기반 피처 생성"""
        df = df.copy()
        
        df['hour'] = df['timestamp'].dt.hour
        df['day'] = df['timestamp'].dt.day
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['month'] = df['timestamp'].dt.month
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        
        return df
    
    def create_lag_features(self, df, column='close', lags=[1, 2, 3, 5, 10]):
        """시차 피처 생성"""
        df = df.copy()
        
        for lag in lags:
            df[f'{column}_lag_{lag}'] = df[column].shift(lag)
        
        return df
    
    def create_rolling_features(self, df, column='close', windows=[5, 10, 20]):
        """롤링 통계 피처 생성"""
        df = df.copy()
        
        for window in windows:
            df[f'{column}_rolling_mean_{window}'] = df[column].rolling(window=window).mean()
            df[f'{column}_rolling_std_{window}'] = df[column].rolling(window=window).std()
            df[f'{column}_rolling_min_{window}'] = df[column].rolling(window=window).min()
            df[f'{column}_rolling_max_{window}'] = df[column].rolling(window=window).max()
        
        return df
```

---

## 4. 데이터 캐싱

### 4.1 캐시 관리

#### [NEW] [data/cache_manager.py](file:///e:/GitHub/UpbitTrader/data/cache_manager.py)

```python
import os
import pickle
from datetime import datetime, timedelta

class CacheManager:
    """데이터 캐시 관리"""
    
    def __init__(self, cache_dir='./data_cache'):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def save_cache(self, key, data, ttl_hours=1):
        """캐시 저장
        
        Args:
            key: 캐시 키
            data: 저장할 데이터
            ttl_hours: 유효 시간 (시간 단위)
        """
        cache_file = os.path.join(self.cache_dir, f"{key}.pkl")
        
        cache_data = {
            'data': data,
            'timestamp': datetime.now(),
            'ttl_hours': ttl_hours
        }
        
        with open(cache_file, 'wb') as f:
            pickle.dump(cache_data, f)
    
    def load_cache(self, key):
        """캐시 로드"""
        cache_file = os.path.join(self.cache_dir, f"{key}.pkl")
        
        if not os.path.exists(cache_file):
            return None
        
        with open(cache_file, 'rb') as f:
            cache_data = pickle.load(f)
        
        # TTL 확인
        timestamp = cache_data['timestamp']
        ttl_hours = cache_data['ttl_hours']
        
        if datetime.now() - timestamp > timedelta(hours=ttl_hours):
            # 만료됨
            os.remove(cache_file)
            return None
        
        return cache_data['data']
    
    def clear_cache(self, key=None):
        """캐시 삭제"""
        if key:
            cache_file = os.path.join(self.cache_dir, f"{key}.pkl")
            if os.path.exists(cache_file):
                os.remove(cache_file)
        else:
            # 전체 캐시 삭제
            for file in os.listdir(self.cache_dir):
                os.remove(os.path.join(self.cache_dir, file))
```

---

## 5. 데이터 파이프라인

### 5.1 통합 파이프라인

#### [NEW] [data/pipeline.py](file:///e:/GitHub/UpbitTrader/data/pipeline.py)

```python
from data.market_data import MarketDataCollector
from data.indicators import IndicatorCalculator
from data.preprocessor import DataPreprocessor
from data.cache_manager import CacheManager

class DataPipeline:
    """데이터 처리 파이프라인"""
    
    def __init__(self, api, db):
        self.collector = MarketDataCollector(api, db)
        self.indicator_calc = IndicatorCalculator()
        self.preprocessor = DataPreprocessor()
        self.cache = CacheManager()
    
    def get_processed_data(self, market, days=30, use_cache=True):
        """처리된 데이터 가져오기"""
        
        cache_key = f"{market}_{days}days"
        
        # 캐시 확인
        if use_cache:
            cached_data = self.cache.load_cache(cache_key)
            if cached_data is not None:
                print(f"💾 캐시에서 {market} 데이터 로드")
                return cached_data
        
        # 1. 데이터 수집
        df = self.collector.collect_historical_data(market, days=days)
        
        # 2. 지표 계산
        df = self.indicator_calc.calculate_all_indicators(df)
        
        # 3. 전처리
        df = self.preprocessor.fill_missing_values(df)
        df = self.preprocessor.create_time_features(df)
        
        # 4. 캐시 저장
        if use_cache:
            self.cache.save_cache(cache_key, df, ttl_hours=1)
        
        return df
```

---

## 검증 체크리스트

### ✅ 데이터 수집
- [ ] 과거 데이터 수집 (30일)
- [ ] 실시간 데이터 수집
- [ ] 다중 마켓 수집
- [ ] 데이터베이스 저장
- [ ] 델타 업데이트

### ✅ 기술적 지표
- [ ] MA, EMA 계산
- [ ] RSI 계산
- [ ] MACD 계산
- [ ] 볼린저 밴드 계산
- [ ] 스토캐스틱 계산
- [ ] ATR, OBV, ADX 계산

### ✅ 전처리
- [ ] 결측치 처리
- [ ] 이상치 제거
- [ ] 정규화/표준화
- [ ] 시간 피처 생성
- [ ] 시차 피처 생성

### ✅ 캐싱
- [ ] 데이터 캐시 저장
- [ ] TTL 관리
- [ ] 캐시 로드
- [ ] 캐시 삭제

---

## 다음 단계

Phase 3 완료 후:
- ✅ Phase 4: AI 모델 개발
- 🤖 LSTM 모델 설계
- 📊 학습 데이터 준비

> [!TIP]
> 기술적 지표는 AI 모델의 입력 피처로 활용됩니다. 다양한 지표를 계산하여 모델의 예측 능력을 향상시킬 수 있습니다.
