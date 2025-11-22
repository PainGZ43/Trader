# Phase 1: 기본 인프라 구축 상세 계획

**목표**: Upbit 자동매매 프로그램의 기반이 되는 인프라 구축

**예상 기간**: 3-5일

---

## 1. 프로젝트 폴더 구조 생성

### 1.1 디렉토리 구조 설계

```
UpbitTrader/
├── main.py                      # 애플리케이션 진입점
├── config.py                    # 설정 관리
├── requirements.txt             # 의존성 패키지
├── .env.example                 # 환경변수 템플릿
├── .gitignore                   # Git 제외 파일
├── README.md                    # 프로젝트 설명
│
├── api/                         # API 관련
│   ├── __init__.py
│   ├── upbit_api.py            # REST API
│   └── upbit_websocket.py      # WebSocket
│
├── data/                        # 데이터 처리
│   ├── __init__.py
│   ├── market_data.py          # 시장 데이터
│   └── indicators.py           # 기술적 지표
│
├── ai/                          # AI 모델
│   ├── __init__.py
│   ├── model.py                # 모델 정의
│   ├── trainer.py              # 학습
│   └── predictor.py            # 예측
│
├── trading/                     # 트레이딩
│   ├── __init__.py
│   ├── engine.py               # 거래 엔진
│   ├── strategy.py             # 전략
│   └── risk_manager.py         # 리스크 관리
│
├── backtest/                    # 백테스팅
│   ├── __init__.py
│   ├── backtester.py           # 백테스팅 엔진
│   └── optimizer.py            # 최적화
│
├── ui/                          # 사용자 인터페이스
│   ├── __init__.py
│   ├── main_window.py          # 메인 윈도우
│   ├── dashboard.py            # 대시보드
│   ├── chart_widget.py         # 차트
│   ├── settings_dialog.py      # 설정
│   └── backtest_window.py      # 백테스팅 UI
│
├── database/                    # 데이터베이스
│   ├── __init__.py
│   ├── db_manager.py           # DB 관리자
│   └── models.py               # 데이터 모델
│
├── notification/                # 알림
│   ├── __init__.py
│   └── kakao_notify.py         # 카카오톡 알림
│
├── utils/                       # 유틸리티
│   ├── __init__.py
│   ├── logger.py               # 로깅
│   └── error_handler.py        # 에러 처리
│
├── tests/                       # 테스트
│   ├── __init__.py
│   ├── test_api.py
│   ├── test_data.py
│   └── test_trading.py
│
├── logs/                        # 로그 파일
├── models/                      # 학습된 AI 모델
├── data_cache/                  # 캐시된 데이터
└── docs/                        # 문서
    ├── api_guide.md
    ├── strategy_guide.md
    └── user_manual.md
```

### 1.2 구현 파일

#### [NEW] [project_setup.py](file:///e:/GitHub/UpbitTrader/project_setup.py)

**목적**: 프로젝트 폴더 구조 자동 생성

**기능**:
- 모든 디렉토리 생성
- `__init__.py` 파일 자동 생성
- `.gitkeep` 파일로 빈 폴더 유지

**주요 코드 구조**:
```python
import os

def create_project_structure():
    """프로젝트 폴더 구조 생성"""
    directories = [
        'api', 'data', 'ai', 'trading', 'backtest',
        'ui', 'database', 'notification', 'utils',
        'tests', 'logs', 'models', 'data_cache', 'docs'
    ]
    
    # 디렉토리 생성 로직
    # __init__.py 파일 생성
    # README 템플릿 생성
```

---

## 2. 의존성 패키지 관리

### 2.1 requirements.txt 작성

#### [NEW] [requirements.txt](file:///e:/GitHub/UpbitTrader/requirements.txt)

**주요 패키지 목록**:

```txt
# API & 네트워크
pyupbit>=0.2.31
requests>=2.28.0
websocket-client>=1.5.0

# GUI
PyQt5>=5.15.9
PyQtChart>=5.15.6

# 데이터 분석
pandas>=2.0.0
numpy>=1.24.0
TA-Lib>=0.4.26

# 차트 및 시각화
matplotlib>=3.7.0
mplfinance>=0.12.9
pyqtgraph>=0.13.0
plotly>=5.14.0

# AI/ML
tensorflow>=2.12.0
scikit-learn>=1.2.0
keras>=2.12.0

# 데이터베이스
SQLAlchemy>=2.0.0

# 유틸리티
python-dotenv>=1.0.0
python-dateutil>=2.8.2
pytz>=2023.3

# 로깅 & 모니터링
colorlog>=6.7.0

# 테스팅
pytest>=7.3.0
pytest-cov>=4.0.0

# 알림 (선택사항)
# requests-oauthlib  # 카카오톡 알림용
```

### 2.2 설치 스크립트

#### [NEW] [install_dependencies.py](file:///e:/GitHub/UpbitTrader/install_dependencies.py)

**목적**: 패키지 자동 설치 및 검증

**기능**:
- requirements.txt 읽기
- pip 업그레이드
- 패키지 설치
- 설치 성공 여부 확인
- TA-Lib 별도 설치 안내 (Windows용)

---

## 3. 환경 설정 시스템

### 3.1 환경 변수 템플릿

#### [NEW] [.env.example](file:///e:/GitHub/UpbitTrader/.env.example)

```env
# Upbit API 키
UPBIT_ACCESS_KEY=your_access_key_here
UPBIT_SECRET_KEY=your_secret_key_here

# 데이터베이스
DB_PATH=./database/trading.db

# 로그 설정
LOG_LEVEL=INFO
LOG_FILE=./logs/trader.log

# AI 모델 설정
MODEL_PATH=./models/
RETRAIN_INTERVAL_DAYS=7

# 트레이딩 설정
MAX_POSITION_SIZE=1000000
STOP_LOSS_PERCENT=5.0
TAKE_PROFIT_PERCENT=10.0

# 알림 설정 (선택사항)
# KAKAO_TOKEN=your_kakao_token_here
# ENABLE_NOTIFICATIONS=True
```

#### [NEW] [.gitignore](file:///e:/GitHub/UpbitTrader/.gitignore)

```gitignore
# 환경 변수
.env

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/

# IDE
.vscode/
.idea/
*.swp

# 데이터베이스
*.db
*.sqlite

# 로그
logs/
*.log

# 모델 파일
models/*.h5
models/*.pkl

# 캐시
data_cache/
.pytest_cache/

# OS
.DS_Store
Thumbs.db
```

### 3.2 설정 관리 모듈

#### [NEW] [config.py](file:///e:/GitHub/UpbitTrader/config.py)

**목적**: 전역 설정 관리

**주요 기능**:
- `.env` 파일 로드
- API 키 관리
- 경로 설정
- 트레이딩 파라미터
- 설정 검증

**주요 클래스 구조**:
```python
from dotenv import load_dotenv
import os

class Config:
    """전역 설정 관리 클래스"""
    
    def __init__(self):
        load_dotenv()
        
        # API 설정
        self.UPBIT_ACCESS_KEY = os.getenv('UPBIT_ACCESS_KEY')
        self.UPBIT_SECRET_KEY = os.getenv('UPBIT_SECRET_KEY')
        
        # 경로 설정
        self.DB_PATH = os.getenv('DB_PATH', './database/trading.db')
        self.MODEL_PATH = os.getenv('MODEL_PATH', './models/')
        self.LOG_FILE = os.getenv('LOG_FILE', './logs/trader.log')
        
        # 트레이딩 설정
        self.MAX_POSITION_SIZE = float(os.getenv('MAX_POSITION_SIZE', 1000000))
        self.STOP_LOSS_PERCENT = float(os.getenv('STOP_LOSS_PERCENT', 5.0))
        
    def validate(self):
        """설정 유효성 검증"""
        if not self.UPBIT_ACCESS_KEY or not self.UPBIT_SECRET_KEY:
            raise ValueError("API 키가 설정되지 않았습니다.")
```

---

## 4. 데이터베이스 스키마 설계

### 4.1 테이블 구조

#### [NEW] [database/schema.sql](file:///e:/GitHub/UpbitTrader/database/schema.sql)

```sql
-- 시장 데이터 테이블
CREATE TABLE IF NOT EXISTS market_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    market VARCHAR(20) NOT NULL,          -- 마켓 코드 (KRW-BTC)
    timestamp DATETIME NOT NULL,          -- 시간
    open REAL NOT NULL,                   -- 시가
    high REAL NOT NULL,                   -- 고가
    low REAL NOT NULL,                    -- 저가
    close REAL NOT NULL,                  -- 종가
    volume REAL NOT NULL,                 -- 거래량
    value REAL NOT NULL,                  -- 거래대금
    UNIQUE(market, timestamp)
);

-- 거래 이력 테이블
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    market VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,            -- bid/ask
    order_type VARCHAR(20) NOT NULL,      -- limit/market
    price REAL,
    volume REAL NOT NULL,
    executed_volume REAL,
    fee REAL,
    status VARCHAR(20),                   -- done/cancelled/wait
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    uuid VARCHAR(50) UNIQUE,              -- Upbit 주문 UUID
    strategy_name VARCHAR(50)
);

-- 포지션 테이블
CREATE TABLE IF NOT EXISTS positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    market VARCHAR(20) NOT NULL UNIQUE,
    entry_price REAL NOT NULL,
    current_price REAL,
    quantity REAL NOT NULL,
    profit_loss REAL,
    profit_loss_percent REAL,
    opened_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- AI 예측 결과 테이블
CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    market VARCHAR(20) NOT NULL,
    timestamp DATETIME NOT NULL,
    predicted_price REAL,
    confidence REAL,                      -- 신뢰도 0-1
    signal VARCHAR(10),                   -- buy/sell/hold
    model_version VARCHAR(20),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 전략 성과 테이블
CREATE TABLE IF NOT EXISTS strategy_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_name VARCHAR(50) NOT NULL,
    market VARCHAR(20),
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    total_profit REAL DEFAULT 0,
    win_rate REAL,
    sharpe_ratio REAL,
    max_drawdown REAL,
    start_date DATE,
    end_date DATE,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 설정 테이블
CREATE TABLE IF NOT EXISTS settings (
    key VARCHAR(50) PRIMARY KEY,
    value TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 로그 테이블
CREATE TABLE IF NOT EXISTS system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level VARCHAR(10),                    -- INFO/WARNING/ERROR
    message TEXT,
    module VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_market_data_market ON market_data(market);
CREATE INDEX IF NOT EXISTS idx_market_data_timestamp ON market_data(timestamp);
CREATE INDEX IF NOT EXISTS idx_trades_market ON trades(market);
CREATE INDEX IF NOT EXISTS idx_trades_created_at ON trades(created_at);
CREATE INDEX IF NOT EXISTS idx_predictions_market_timestamp ON predictions(market, timestamp);
```

### 4.2 데이터베이스 관리자

#### [NEW] [database/db_manager.py](file:///e:/GitHub/UpbitTrader/database/db_manager.py)

**목적**: 데이터베이스 연결 및 CRUD 관리

**주요 기능**:
- SQLite 연결 관리
- 테이블 생성 및 초기화
- CRUD 작업 메서드
- 트랜잭션 관리
- 쿼리 헬퍼 함수

**주요 메서드**:
```python
class DatabaseManager:
    def __init__(self, db_path):
        """데이터베이스 연결 초기화"""
        
    def initialize_database(self):
        """스키마 생성 및 초기화"""
        
    def insert_market_data(self, market, timestamp, ohlcv):
        """시장 데이터 삽입"""
        
    def get_market_data(self, market, start_date, end_date):
        """시장 데이터 조회"""
        
    def insert_trade(self, trade_info):
        """거래 이력 저장"""
        
    def get_open_positions(self):
        """현재 오픈 포지션 조회"""
        
    def update_position(self, market, current_price):
        """포지션 업데이트"""
```

#### [NEW] [database/models.py](file:///e:/GitHub/UpbitTrader/database/models.py)

**목적**: 데이터 모델 정의 (ORM 스타일)

**주요 클래스**:
- `MarketData`: 시장 데이터
- `Trade`: 거래 기록
- `Position`: 포지션
- `Prediction`: AI 예측
- `StrategyPerformance`: 전략 성과

---

## 5. 기본 유틸리티 구현

### 5.1 로깅 시스템

#### [NEW] [utils/logger.py](file:///e:/GitHub/UpbitTrader/utils/logger.py)

**목적**: 통합 로깅 시스템

**주요 기능**:
- 파일 + 콘솔 동시 출력
- 로그 레벨별 색상 구분
- 로그 파일 순환 (Rotation)
- 모듈별 로거 생성

**구현 예시**:
```python
import logging
from colorlog import ColoredFormatter

def setup_logger(name, log_file, level=logging.INFO):
    """로거 설정"""
    
    # 컬러 포맷터
    console_formatter = ColoredFormatter(
        '%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(message)s',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    
    # 파일 포맷터
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 핸들러 설정
    # 로거 반환
```

### 5.2 에러 핸들러

#### [NEW] [utils/error_handler.py](file:///e:/GitHub/UpbitTrader/utils/error_handler.py)

**목적**: 전역 예외 처리

**주요 기능**:
- 커스텀 예외 클래스
- API 에러 처리
- 재시도 로직
- 에러 알림

**커스텀 예외**:
```python
class UpbitAPIError(Exception):
    """Upbit API 에러"""
    
class InsufficientBalanceError(Exception):
    """잔고 부족 에러"""
    
class OrderExecutionError(Exception):
    """주문 실행 에러"""
```

---

## 6. Git 설정

### 6.1 Git 초기화

```bash
git init
git add .
git commit -m "Initial commit: Project infrastructure setup"
```

### 6.2 README 작성

#### [NEW] [README.md](file:///e:/GitHub/UpbitTrader/README.md)

**포함 내용**:
- 프로젝트 소개
- 주요 기능
- 설치 방법
- 사용 방법
- 라이선스 및 면책조항

---

## 검증 체크리스트

### ✅ 폴더 구조
- [ ] 모든 디렉토리 생성 확인
- [ ] `__init__.py` 파일 존재 확인
- [ ] `.gitignore` 작동 확인

### ✅ 의존성
- [ ] `requirements.txt` 작성 완료
- [ ] 모든 패키지 설치 성공
- [ ] TA-Lib 설치 확인 (Windows)
- [ ] import 테스트 통과

### ✅ 환경 설정
- [ ] `.env.example` 생성
- [ ] `config.py` 동작 확인
- [ ] API 키 로드 테스트
- [ ] 설정 검증 기능 작동

### ✅ 데이터베이스
- [ ] SQLite 파일 생성
- [ ] 모든 테이블 생성 확인
- [ ] CRUD 작업 테스트
- [ ] 인덱스 생성 확인

### ✅ 유틸리티
- [ ] 로거 기능 테스트
- [ ] 로그 파일 생성 확인
- [ ] 에러 핸들러 동작 확인

---

## 다음 단계

Phase 1 완료 후:
- ✅ Phase 2: Upbit API 통합 시작
- 📝 API 테스트 계획 수립
- 🔑 API 키 발급 및 등록

> [!TIP]
> Phase 1은 전체 프로젝트의 기반이므로 꼼꼼하게 구축하세요. 특히 데이터베이스 스키마는 나중에 변경하기 어려우므로 충분히 검토하세요.

> [!IMPORTANT]
> API 키는 절대 Git에 커밋하지 마세요. `.env` 파일은 `.gitignore`에 포함되어 있는지 반드시 확인하세요.
