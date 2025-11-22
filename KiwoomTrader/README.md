# Premium Kiwoom AI Trader 🚀

고급 AI 기반 자동 매매 시스템 (LSTM + XGBoost + Sentiment 앙상블)

**⚡ 키움 REST API 완전 지원!**

## ✨ 주요 기능

- 🤖 **고급 AI 예측**: LSTM + XGBoost + 감성분석 앙상블
- 📊 **실시간 백테스트**: 전략 최적화 및 성능 검증
- 🎯 **자동 매매**: AI 기반 자동 주식 거래
- 📈 **기술적 분석**: 22개 이상의 고급 지표
- 🔍 **종목 검색**: 빠른 종목 찾기
- ⚙️ **UI 내 AI 학습**: 클릭 한 번으로 모델 학습
- 🔌 **키움 REST API**: 실전/모의투자 완벽 지원

## 🚀 빠른 시작 (신규!)

### 📌 필수 요구사항

- **Python**: 3.8 ~ 3.11 (3.12 지원 안함)
- **OS**: Windows 10/11
- **키움증권 계좌** (실전 거래 시)
- **키움 API 승인** (APP_KEY, SECRET_KEY)

### 1️⃣ 설치

가장 쉬운 방법: **`start.bat`** 더블클릭!

또는 수동 설치:
```bash
# 1. 라이브러리 설치
install.bat

# 또는
pip install -r requirements.txt
```

### 🔑 키움 REST API 설정 (신규!)

```bash
# 대화형 설정 도우미
setup_env.bat
```

또는 수동 설정:
1. `.env.example` 복사 → `.env`
2. APP_KEY, SECRET_KEY 입력
3. 계좌번호 입력

**자세한 가이드**: [QUICK_START.md](QUICK_START.md)

### 2️⃣ AI 모델 학습

**방법 1: UI에서 학습 (권장)**
```bash
# 프로그램 실행
run.bat

# 설정 탭 → AI 모델 학습 → 🚀 학습 시작
```

**방법 2: 배치 파일**
```bash
train.bat
```

**방법 3: 명령줄**
```bash
python train_ai.py 005930 1y 1h
```

**학습 시간**: 약 10-15분

### 3️⃣ 실행

```bash
run.bat
```

또는 통합 메뉴:
```bash
start.bat
```

## 📂 프로젝트 구조

```
kiwoom_rest_trader/
├── ai/                          # AI 모듈
│   ├── predictor.py            # 메인 AI 예측기
│   ├── lstm_model.py           # LSTM 딥러닝 모델
│   ├── xgboost_model.py        # XGBoost 분류 모델
│   ├── ensemble_predictor.py   # 앙상블 통합
│   ├── indicators.py           # 기술적 지표 (22개)
│   ├── data_collector.py       # 데이터 수집기
│   ├── sentiment.py            # 감성 분석
│   └── backtester.py           # 백테스팅 엔진
├── ui/                          # UI
│   ├── main_window.py          # 메인 윈도우
│   └── styles.qss              # 스타일시트
├── models/                      # 학습된 모델 저장
│   ├── lstm_model.h5
│   └── xgboost_model.pkl
├── data/                        # 캐시된 데이터
├── logs/                        # 로그 파일
├── main.py                      # 메인 실행 파일
├── train_ai.py                  # AI 학습 스크립트
├── trading_manager.py           # 트레이딩 매니저
├── kiwoom_api.py               # Kiwoom API
├── requirements.txt             # 의존성
├── start.bat                    # 통합 메뉴 🌟
├── run.bat                      # 프로그램 실행
├── train.bat                    # AI 학습
└── install.bat                  # 설치
```

## 🎮 사용 방법

### 배치 파일 모음

| 파일 | 설명 | 사용 시점 |
|------|------|----------|
| **`start.bat`** | 📋 통합 메뉴 | **가장 편리!** |
| `install.bat` | 📦 라이브러리 설치 | 최초 1회 |
| `train.bat` | 🤖 AI 학습 | 모델 학습 필요 시 |
| `run.bat` | ▶️ 프로그램 실행 | 매번 실행 |

### start.bat 메뉴

```
═══════════════════════════════
  Premium Kiwoom AI Trader
  간편 실행 메뉴
═══════════════════════════════

[1] 프로그램 실행
[2] AI 모델 학습
[3] 라이브러리 설치
[4] 백테스트만 실행
[5] 종료
```

### UI 기능

#### 1. 대시보드
- 계좌 정보
- 보유 종목
- 실시간 수익률

#### 2. 백테스트
- **백테스트 실행**: 전략 테스트
- **🚀 전략 최적화**: 1,024개 조합 테스트하여 최적 파라미터 자동 탐색
- **일별 매매 요약**: 매수/매도 색상 구분, 손익 표시

#### 3. 설정
- **🤖 AI 모델 학습**: UI에서 직접 학습 가능
  - 종목 코드 선택
  - 학습 기간 선택 (6mo/1y/2y/5y)
  - 데이터 간격 선택 (1h/1d)
  - 실시간 진행률 표시
  - 학습 결과 확인

## 🤖 AI 시스템

### 앙상블 구조

```
LSTM (40%)          시계열 패턴 학습
     +
XGBoost (35%)       기술적 지표 분석
     +
Sentiment (25%)     뉴스/소셜 감성
     ↓
최종 예측 점수 (0-1)
```

### 학습 데이터

- **출처**: Yahoo Finance (yfinance)
- **종목**: 한국 주식 (예: 005930.KS)
- **기간**: 6개월 ~ 5년
- **간격**: 1시간봉 권장

### 성능 (예상)

- **백테스트 승률**: 55-65%
- **예측 정확도**: 60-68%
- **MDD 개선**: 20-30% 감소

## 📊 백테스트

### 전략 최적화

"🚀 전략 최적화" 버튼 클릭 시:
- **테스트 조합**: 1,024개 (4⁵)
- **최적화 파라미터**:
  - 볼륨 임계값
  - AI 점수 임계값
  - 익절/손절 목표
  - 쿨다운 시간
- **소요 시간**: 약 5-10분

### 결과 분석

- 상위 5개 전략 비교
- 매수/매도 횟수 (색상 구분)
- 일별 손익 요약
- Feature Importance

## ⚙️ 설정

### AI 모델 재학습

**권장 주기**: 주 1회

```bash
# 매주 일요일
train.bat
```

### 파라미터 튜닝

`ai/strategy_optimizer.py`:
```python
param_grid = {
    'vol_threshold': [0.05, 0.08, 0.10, 0.15],
    'ai_threshold': [0.60, 0.65, 0.70, 0.75],
    'take_profit': [2.0, 3.0, 4.0, 5.0],
    'stop_loss': [1.0, 1.5, 2.0, 2.5],
    'cooldown': [30, 60, 90, 120],
}
```

## 🛠️ 문제 해결

### Q: 모듈을 찾을 수 없습니다
**A**: 라이브러리 재설치
```bash
install.bat
```

### Q: TensorFlow 설치 오류
**A**: Python 3.8-3.11 사용 (3.12 불가)
```bash
python --version
```

### Q: 모델이 로드되지 않습니다
**A**: AI 학습 먼저 실행
```bash
train.bat
```

### Q: GPU 사용하고 싶어요
**A**: TensorFlow GPU 버전 설치
```bash
pip install tensorflow[and-cuda]==2.15.0
```

## 📝 로그

`logs/kiwoom_trader.log`에서 확인

## 🔒 보안

- API 키는 `.env` 파일에 저장
- `.gitignore`에 포함되어 버전 관리 제외

## 📄 라이선스

개인 사용 목적

## 🙏 감사

- yfinance: 데이터 수집
- TensorFlow: LSTM
- XGBoost: 분류
- PyQt5: UI

---

**🚀 즐거운 트레이딩 되세요!**
