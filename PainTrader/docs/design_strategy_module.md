# 상세 설계: AI 및 전략 엔진 모듈

## 1. 개요
이 모듈은 수집된 시장 데이터를 분석하여 매수/매도 의사결정을 내리는 시스템의 **두뇌**입니다. 사용자는 다양한 전략과 AI 모델을 플러그인처럼 교체하여 사용할 수 있습니다.

## 2. 핵심 컴포넌트

### 2.1. Strategy Interface (전략 인터페이스)
모든 매매 전략은 이 추상 클래스를 상속받아 구현해야 합니다.

```python
class Strategy(ABC):
    @abstractmethod
    def process(self, market_data: pd.DataFrame) -> Signal:
        """
        시장 데이터를 입력받아 매매 신호를 생성합니다.
        Returns: Signal(action=BUY/SELL/HOLD, price=..., quantity=...)
        """
        pass

    @abstractmethod
    def setup(self, config: dict):
        """전략 파라미터 초기화"""
        pass
```

### 2.2. Built-in Strategies (내장 전략)
1.  **Volatility Breakout (변동성 돌파)**
    *   **로직**: (전일 고가 - 전일 저가) * k + 금일 시가 돌파 시 매수.
    *   **파라미터**: `k` (0.5 ~ 1.0), `ma_filter` (이동평균선 추세 필터 여부).
2.  **Moving Average Crossover (이동평균 교차)**
    *   **로직**: 단기 이평선이 장기 이평선을 상향 돌파(Golden Cross) 시 매수, 하향 돌파(Dead Cross) 시 매도.
    *   **파라미터**: `short_window` (예: 5), `long_window` (예: 20).
3.  **RSI Mean Reversion (RSI 역추세)**
    *   **로직**: RSI가 30 미만(과매도)일 때 매수, 70 초과(과매수)일 때 매도.
    *   **파라미터**: `rsi_period` (14), `buy_threshold` (30), `sell_threshold` (70).
4.  **Bollinger Band Trend Following (볼린저 밴드 추세)**
    *   **로직**: 가격이 상단 밴드를 돌파하면 매수, 하단 밴드를 이탈하면 매도 (또는 반대).
    *   **파라미터**: `window` (20), `num_std` (2).
5.  **AI Hybrid (AI 하이브리드)**
    *   **로직**: 기본 기술적 지표 시그널 + AI 예측 점수(Confidence) > 임계값 일 때 진입.
    *   **파라미터**: `ai_model_path`, `threshold` (0.7 이상 등).

### 2.3. AI Engine (AI 엔진)
*   **역할**: 독립적으로 동작하며 시장 상황을 분석하고 예측값을 생성하는 **공용 서비스**입니다.
*   **활용**:
    *   **AI Hybrid 전략**: AI 예측값이 메인 진입 근거가 됨.
    *   **일반 전략 (RSI, 변동성 돌파 등)**: AI 예측값을 **필터(Filter)**로 사용 가능. (예: RSI 매수 신호가 떴어도 AI가 '하락'을 예측하면 진입 보류).
*   **Model Loader**: PyTorch/TensorFlow 모델 파일(.pt, .h5)을 로드.
*   **Feature Extractor**: OHLCV 데이터에서 AI 모델 입력용 텐서(Tensor)로 변환.
*   **Predictor (추론 능력)**:
    1.  **가격 예측 (Regression)**: "다음 10분 뒤 종가는 얼마일까?" (LSTM/Transformer).
    2.  **추세 분류 (Classification)**: "앞으로 오를까(Up), 내릴까(Down), 횡보할까(Flat)?" (CNN/Transformer).
    3.  **변동성 예측 (Volatility)**: "앞으로 가격이 얼마나 요동칠까?" (Risk 관리용).
    4.  **강화학습 행동 (RL Action)**: "지금 상황(State)에서 살까(Buy), 팔까(Sell), 관망할까(Hold)?" (PPO/DQN).

### 2.4. AI 연동 인터페이스 (AI Integration Interface)
전략이 AI 엔진을 쉽게 사용할 수 있도록 표준화된 인터페이스를 제공합니다.

```python
class AIEngine:
    def get_prediction(self, symbol: str, market_data: pd.DataFrame) -> float:
        """
        특정 종목의 향후 상승 확률(0.0 ~ 1.0)을 반환
        """
        features = self.preprocess(market_data)
        return self.model.predict(features)

# 전략 내부 사용 예시
class MyStrategy(Strategy):
    def process(self, data):
        # 1. 기술적 지표 계산
        rsi = talib.RSI(data['close'])
        
        # 2. AI 예측값 조회 (필터)
        ai_score = self.ai_engine.get_prediction("005930", data)
        
        # 3. 최종 판단
        if rsi < 30 and ai_score > 0.8:
            return Signal.BUY
```

### 2.5. Technical Analysis (TA) Engine (기술적 분석 엔진)
기본적인 지표 시그널은 **수학적 계산**과 **조건문**을 통해 파악합니다.

1.  **계산 (Calculation)**: `TA-Lib` 또는 `pandas-ta` 라이브러리를 사용하여 OHLCV 데이터로부터 지표값을 산출합니다.
    *   *예시*: `RSI = talib.RSI(close_prices, timeperiod=14)` -> 결과: 25.5
2.  **판단 (Evaluation)**: 산출된 값과 사전 정의된 **임계값(Threshold)**을 비교합니다.
    *   *예시*: `if RSI < 30: return Signal.BUY` (과매도 구간이므로 매수)
3.  **조합 (Combination)**: 여러 지표의 신호를 AND/OR 조건으로 결합하여 최종 신뢰도를 높입니다.
    *   *예시*: `if (RSI < 30) and (Price > MA20): return Signal.BUY` (눌림목 매수)

### 2.5. AI Training Data (AI 학습 데이터)
AI 모델이 학습할 데이터(Feature)는 크게 3가지 카테고리로 나뉩니다.

1.  **기본 시세 데이터 (Raw Market Data)**
    *   **OHLCV**: 시가, 고가, 저가, 종가, 거래량 (가장 기초).
    *   **호가창 (Orderbook)**: 매수/매도 1~5호가 잔량 및 비율 (단기 수급 파악용).
    *   **체결강도**: 매수 체결 vs 매도 체결 비율.
2.  **기술적 지표 (Technical Indicators)**
    *   **추세**: 이동평균선(MA), MACD, Parabolic SAR.
    *   **모멘텀**: RSI, Stochastic.
    *   **변동성**: Bollinger Bands, ATR.
    *   **거래량**: OBV, MFI.
3.  **거시/보조 데이터 (Macro/Auxiliary) - 필수 (Required)**
    *   **시장 지수**: 코스피/코스닥 지수, 나스닥 선물 (시장 분위기 파악).
    *   **환율**: 원/달러 환율 (수출주/수입주 영향 분석).
    *   **시간 정보**: 요일, 시간대(장시작/장마감 부근 등).

### 2.6. 매매 대상 및 시간 관리 (Target & Schedule)
*   **종목 선정 (Target Universe)**: 누가 매매할 종목을 고르는가?
    1.  **사용자 지정 (User Watchlist)**: 사용자가 직접 등록한 종목만 매매.
    2.  **조건검색 (Condition Search)**: 키움증권 조건검색식에 포착된 종목을 실시간으로 편입.
    3.  **AI 추천 (AI Recommendation)**: 전날 밤 AI가 분석하여 "내일 오를 것 같은 종목 Top 10" 선정.
    *   **필터링 (Filtering)**:
        *   **유동성 필터 (Liquidity Filter)**: 평균 거래대금(예: 100억 미만) 또는 거래량 부족 종목 자동 제외 (슬리피지 방지).
        *   **관리종목 필터**: 관리/환기/거래정지 종목 자동 제외.
*   **매매 시간 (Trading Schedule)**: 언제 매매하는가?
    1.  **전체 장 운영 시간**: 09:00 ~ 15:30.
    2.  **피크 타임 (Peak Time)**: 유동성이 풍부한 09:00 ~ 10:00 집중 매매.
    3.  **AI 타이밍**: AI가 "지금이 기회"라고 판단할 때만 (시간 무관).

## 3. 정밀 백테스터 (Precision Backtester)

### 3.1. 시뮬레이션 엔진 (Simulation Engine)
*   **Event-Driven 방식**: 과거 데이터를 한 줄씩(Bar-by-Bar) 읽으며 실제 장중과 동일한 이벤트 흐름으로 시뮬레이션. (미래 참조 편향 방지).
*   **정교한 체결 로직 (Order Matching)**:
    *   **시장가 (Market)**: 다음 봉 시가(Open) 또는 현재 봉 종가(Close)에 슬리피지 반영하여 즉시 체결.
    *   **지정가 (Limit)**: `Low <= Limit Price <= High` 조건 만족 시 체결. (보수적 관점 적용).
    *   **수수료/세금**: 키움증권 수수료(0.015%) + 증권거래세(0.20%) 자동 차감.

### 3.2. 성과 분석 (Performance Metrics)
*   **수익성**: 누적 수익률(CAGR), 손익비(Profit Factor), 평균 수익률.
*   **안정성**: **MDD (Maximum Drawdown)**, Sharpe Ratio, Sortino Ratio.
*   **승률**: 전체 거래 중 수익 거래 비율.

### 3.3. 전략 최적화 (Optimization)
*   **Grid Search**: 파라미터(예: 이평선 기간 5~60)를 일정 간격으로 모두 테스트하여 최적값 도출.
*   **Walk-Forward Analysis**: 과거 최적값이 미래에도 통하는지 검증 (과적합 방지).

### 3.4. 시각화 (Visualization)
*   **Equity Curve**: 자산 증감 그래프 (벤치마크 지수와 비교).
*   **Drawdown Chart**: 낙폭 구간 시각화.
*   **Trade Markers**: 차트 위에 매수/매도 시점 표시.

## 4. 데이터 흐름
1.  `Data Manager` -> `Strategy Engine` (실시간 틱/분봉 전달)
2.  `Strategy Engine` -> `AI Engine` (필요 시 예측 요청)
3.  `Strategy Engine` -> `Signal` 생성
4.  `Signal` -> `Risk Manager` (자금 관리 확인) -> `Order Manager`

## 5. AI 엔진 심화 고려사항 (Advanced AI Considerations)

### 5.1. 과적합 방지 (Overfitting Prevention)
*   **이슈**: AI가 과거 데이터를 달달 외워서 백테스트 수익률은 100%인데 실전에서 망하는 현상.
*   **해결**:
    *   **Walk-Forward Validation**: 데이터를 과거->미래 순으로 롤링하며 검증.
    *   **Dropout & Regularization**: 모델 학습 시 일부 뉴런을 꺼서 일반화 성능 향상.
    *   **Feature Selection**: 너무 많은 지표(Noise) 대신 핵심 지표만 선별하여 입력.

### 5.2. 컨셉 드리프트 (Concept Drift) 대응
*   **이슈**: 시장의 성격(상승장/하락장/횡보장)이 바뀌면 옛날 모델은 바보가 됨.
*   **해결**:
    *   **지속적 재학습 (Continuous Retraining)**: 매주/매달 최신 데이터로 모델 업데이트.
    *   **Regime Detection**: 현재 시장 상황(Regime)을 먼저 분류하고, 그에 맞는 특화 모델(Bull/Bear Model)을 스위칭.

### 5.3. 추론 지연 (Inference Latency)
*   **이슈**: 실시간 단타인데 AI가 생각하느라 1초 걸리면 이미 늦음.
*   **해결**:
    *   **모델 경량화**: 거대한 Transformer 대신 GRU/LSTM 사용하거나 모델 크기 축소.
    *   **TensorRT / ONNX**: 학습된 모델을 추론 전용 포맷으로 변환하여 속도 10배 향상.

### 5.4. 데이터 정규화 (Data Normalization)
*   **이슈**: 삼성전자(70,000원)와 비트코인(1억)의 가격 단위가 달라 AI가 혼란스러워함.
*   **해결**:
    *   **Log Return**: 절대 가격 대신 '변화율(%)'을 입력으로 사용.
    *   **Z-Score / MinMax**: 모든 지표를 0~1 또는 -1~1 사이로 스케일링.

## 6. 테스트 계획 (Testing Plan)

### 6.1. 단위 테스트 (Unit Test)
*   **지표 정확성**: TA-Lib 계산 결과와 수기 계산(또는 엑셀) 결과 일치 여부 검증.
*   **전략 로직**: 특정 상황(예: 골든크로스)을 가정한 Mock 데이터를 주입했을 때 `Signal.BUY`가 발생하는지 검증.

### 6.2. AI 모델 테스트
*   **입출력 검증**: 모델에 더미 텐서(Dummy Tensor)를 넣었을 때 에러 없이 출력값이 나오는지 확인.
*   **속도 측정**: 추론(Inference) 시간이 허용 범위(예: 100ms) 이내인지 측정.

### 6.3. 백테스터 검증
*   **무결성 확인**: 미래 데이터를 참조(Look-ahead)하는지 확인하기 위해, 랜덤 데이터로 테스트.
*   **체결 로직**: 상한가/하한가 등 극단적인 상황에서 주문이 거부되거나 체결되지 않는지 확인.

## 7. 전략 상태 영속성 (State Persistence)
*   **이슈**: 프로그램이 장중에 재시작되면, "내가 이 종목을 왜 샀는지(진입 근거)", "손절가는 얼마였는지" 다 까먹음.
*   **해결**:
    *   **Context Saving**: 매수 시점의 전략 상태(진입가, 목표가, 손절가, 진입 전략명)를 DB(`trade_history`)에 JSON 형태로 저장.
    *   **Context Loading**: 프로그램 시작 시, 보유 종목이 있다면 DB에서 해당 종목의 매수 컨텍스트를 로드하여 전략 복원.
