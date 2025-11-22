# Phase 5-9: 통합 상세 계획

본 문서는 Phase 5부터 Phase 9까지의 상세 계획을 통합하여 제공합니다.

---

# Phase 5: 트레이딩 로직

**목표**: 실제 주문 실행 및 리스크 관리 시스템 구축

**예상 기간**: 4-6일

## 1. 트레이딩 엔진

### [NEW] [trading/engine.py](file:///e:/GitHub/UpbitTrader/trading/engine.py)

**주요 클래스**: `TradingEngine`

**핵심 기능**:
```python
class TradingEngine:
    def __init__(self, api, db, config):
        self.api = api
        self.db = db
        self.config = config
        self.positions = {}  # 현재 포지션
        self.orders = []     # 주문 내역
        
    def execute_buy(self, market, amount, price=None):
        """매수 실행"""
        # 1. 잔고 확인
        # 2. 리스크 검증
        # 3. 주문 실행
        # 4. DB 저장
        
    def execute_sell(self, market, volume, price=None):
        """매도 실행"""
        # 1. 포지션 확인
        # 2. 주문 실행
        # 3. 포지션 업데이트
        # 4. DB 저장
        
    def update_positions(self):
        """포지션 업데이트"""
        # 현재가 조회하여 손익 계산
        
    def check_stop_loss_take_profit(self):
        """손절/익절 체크"""
        # 각 포지션별 손절/익절 조건 확인
```

## 2. 전략 관리

### [NEW] [trading/strategy.py](file:///e:/GitHub/UpbitTrader/trading/strategy.py)

**전략 베이스 클래스**:
```python
class BaseStrategy:
    def __init__(self, name):
        self.name = name
        
    def generate_signal(self, data):
        """시그널 생성 (추상 메서드)"""
        raise NotImplementedError

class AIStrategy(BaseStrategy):
    """AI 기반 전략"""
    def __init__(self, predictor):
        super().__init__("AI Strategy")
        self.predictor = predictor
        
    def generate_signal(self, data):
        # AI 예측 기반 시그널
        pred = self.predictor.predict(data)
        # ... 시그널 로직

class RSIStrategy(BaseStrategy):
    """RSI 기반 전략"""
    def generate_signal(self, data):
        rsi = data['rsi'].iloc[-1]
        if rsi < 30:
            return 'buy'
        elif rsi > 70:
            return 'sell'
        return 'hold'

class ComboStrategy(BaseStrategy):
    """복합 전략 (AI + 기술적 지표)"""
    def generate_signal(self, data):
        # AI 예측 + RSI + MACD 등 종합 판단
        pass
```

## 3. 리스크 관리

### [NEW] [trading/risk_manager.py](file:///e:/GitHub/UpbitTrader/trading/risk_manager.py)

```python
class RiskManager:
    """리스크 관리 클래스"""
    
    def __init__(self, config):
        self.max_position_size = config.MAX_POSITION_SIZE
        self.stop_loss_percent = config.STOP_LOSS_PERCENT
        self.take_profit_percent = config.TAKE_PROFIT_PERCENT
        self.max_daily_loss = config.MAX_DAILY_LOSS
        
    def calculate_position_size(self, balance, risk_per_trade=0.02):
        """포지션 사이즈 계산"""
        return min(balance * risk_per_trade, self.max_position_size)
    
    def calculate_stop_loss(self, entry_price):
        """손절가 계산"""
        return entry_price * (1 - self.stop_loss_percent / 100)
    
    def calculate_take_profit(self, entry_price):
        """익절가 계산"""
        return entry_price * (1 + self.take_profit_percent / 100)
    
    def check_daily_loss_limit(self, today_profit_loss):
        """일일 손실 한도 체크"""
        if today_profit_loss < -self.max_daily_loss:
            return False  # 거래 중단
        return True
```

**검증 체크리스트**:
- [ ] 매수/매도 실행 테스트
- [ ] 포지션 관리
- [ ] 전략 시그널 생성
- [ ] 손절/익절 자동 실행
- [ ] 리스크 한도 검증

---

# Phase 6: 백테스팅 시스템

**목표**: 전략 검증 및 성과 분석

**예상 기간**: 4-5일

## 1. 백테스팅 엔진

### [NEW] [backtest/backtester.py](file:///e:/GitHub/UpbitTrader/backtest/backtester.py)

```python
class Backtester:
    """백테스팅 엔진"""
    
    def __init__(self, strategy, initial_balance=10000000):
        self.strategy = strategy
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.positions = {}
        self.trades = []
        
    def run(self, data):
        """백테스트 실행"""
        for i in range(len(data)):
            # 1. 시그널 생성
            signal = self.strategy.generate_signal(data[:i+1])
            
            # 2. 주문 실행 (시뮬레이션)
            if signal == 'buy':
                self._simulate_buy(data.iloc[i])
            elif signal == 'sell':
                self._simulate_sell(data.iloc[i])
            
            # 3. 포지션 업데이트
            self._update_positions(data.iloc[i])
        
        # 결과 분석
        return self.analyze_results()
    
    def analyze_results(self):
        """성과 분석"""
        total_return = (self.balance - self.initial_balance) / self.initial_balance
        
        # 승률 계산
        winning_trades = [t for t in self.trades if t['profit'] > 0]
        win_rate = len(winning_trades) / len(self.trades) if self.trades else 0
        
        # MDD 계산
        equity_curve = self._calculate_equity_curve()
        mdd = self._calculate_mdd(equity_curve)
        
        # 샤프 비율
        sharpe = self._calculate_sharpe_ratio()
        
        return {
            'total_return': total_return * 100,
            'final_balance': self.balance,
            'total_trades': len(self.trades),
            'win_rate': win_rate * 100,
            'mdd': mdd * 100,
            'sharpe_ratio': sharpe
        }
```

## 2. 전략 최적화

### [NEW] [backtest/optimizer.py](file:///e:/GitHub/UpbitTrader/backtest/optimizer.py)

```python
from itertools import product

class StrategyOptimizer:
    """전략 파라미터 최적화"""
    
    def grid_search(self, strategy_class, data, param_grid):
        """그리드 서치"""
        best_result = None
        best_params = None
        best_score = -float('inf')
        
        # 파라미터 조합 생성
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        
        for params in product(*param_values):
            param_dict = dict(zip(param_names, params))
            
            # 전략 생성
            strategy = strategy_class(**param_dict)
            
            # 백테스트
            backtester = Backtester(strategy)
            result = backtester.run(data)
            
            # 점수 계산 (샤프 비율 기준)
            score = result['sharpe_ratio']
            
            if score > best_score:
                best_score = score
                best_params = param_dict
                best_result = result
        
        return {
            'best_params': best_params,
            'best_result': best_result,
            'best_score': best_score
        }
```

**검증 체크리스트**:
- [ ] 백테스트 실행
- [ ] 성과 지표 계산
- [ ] 파라미터 최적화
- [ ] 결과 리포트 생성
- [ ] 시각화

---

# Phase 7: 사용자 인터페이스

**목표**: PyQt5 기반 GUI 구축

**예상 기간**: 6-7일

## 1. 메인 윈도우

### [NEW] [ui/main_window.py](file:///e:/GitHub/UpbitTrader/ui/main_window.py)

```python
from PyQt5.QtWidgets import QMainWindow, QTabWidget, QAction, QMenuBar
from ui.dashboard import DashboardWidget
from ui.chart_widget import ChartWidget
from ui.backtest_window import BacktestWidget

class MainWindow(QMainWindow):
    """메인 윈도우"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Upbit Auto Trader")
        self.setGeometry(100, 100, 1600, 900)
        
        self.init_ui()
        
    def init_ui(self):
        # 메뉴 바
        self.create_menu_bar()
        
        # 탭 위젯
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # 탭 추가
        self.tabs.addTab(DashboardWidget(), "대시보드")
        self.tabs.addTab(ChartWidget(), "차트")
        self.tabs.addTab(BacktestWidget(), "백테스팅")
        
    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # 파일 메뉴
        file_menu = menubar.addMenu('파일')
        file_menu.addAction(QAction('설정', self))
        file_menu.addAction(QAction('종료', self))
        
        # 거래 메뉴
        trading_menu = menubar.addMenu('거래')
        trading_menu.addAction(QAction('시작', self))
        trading_menu.addAction(QAction('중지', self))
```

## 2. 대시보드

### [NEW] [ui/dashboard.py](file:///e:/GitHub/UpbitTrader/ui/dashboard.py)

**주요 구성**:
- 계좌 잔고 표시
- 현재 포지션 목록
- 최근 거래 이력
- 수익/손실 현황
- 실시간 시세 (Top 10)

## 3. 차트 위젯

### [NEW] [ui/chart_widget.py](file:///e:/GitHub/UpbitTrader/ui/chart_widget.py)

**기능**:
- 실시간 캔들 차트
- 기술적 지표 오버레이 (MA, RSI, MACD)
- AI 예측 표시
- 매매 시그널 마커
- 볼륨 차트

**라이브러리**: `mplfinance`, `pyqtgraph`

## 4. 설정 대화상자

### [NEW] [ui/settings_dialog.py](file:///e:/GitHub/UpbitTrader/ui/settings_dialog.py)

**설정 항목**:
- API 키 입력
- 트레이딩 파라미터
- 리스크 관리 설정
- 알림 설정
- 전략 선택

**검증 체크리스트**:
- [ ] 메인 윈도우 레이아웃
- [ ] 대시보드 동작
- [ ] 실시간 차트 업데이트
- [ ] 설정 저장/로드
- [ ] 반응형 디자인

---

# Phase 8: 알림 및 모니터링

**목표**: 카카오톡 알림 및 로깅 시스템

**예상 기간**: 2-3일

## 1. 카카오톡 알림

### [NEW] [notification/kakao_notify.py](file:///e:/GitHub/UpbitTrader/notification/kakao_notify.py)

```python
import requests

class KakaoNotifier:
    """카카오톡 알림"""
    
    def __init__(self, token):
        self.token = token
        self.url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
        
    def send_message(self, message):
        """메시지 전송"""
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        
        data = {
            "template_object": {
                "object_type": "text",
                "text": message,
                "link": {
                    "web_url": "https://upbit.com"
                }
            }
        }
        
        response = requests.post(self.url, headers=headers, json=data)
        return response.status_code == 200
    
    def notify_trade(self, market, side, price, volume):
        """거래 알림"""
        message = f"""
🔔 거래 체결
마켓: {market}
구분: {'매수' if side == 'bid' else '매도'}
가격: {price:,}원
수량: {volume}
        """
        self.send_message(message)
    
    def notify_profit_loss(self, market, profit_loss, percent):
        """손익 알림"""
        emoji = "📈" if profit_loss > 0 else "📉"
        message = f"{emoji} {market} 손익: {profit_loss:,}원 ({percent:+.2f}%)"
        self.send_message(message)
```

## 2. 로깅 강화

### [MODIFY] [utils/logger.py](file:///e:/GitHub/UpbitTrader/utils/logger.py)

**추가 기능**:
- 거래 전용 로그
- 에러 로그 자동 알림
- 로그 레벨별 파일 분리
- 로그 압축 및 아카이빙

**검증 체크리스트**:
- [ ] 카카오톡 토큰 발급
- [ ] 메시지 전송 테스트
- [ ] 거래 알림 자동화
- [ ] 로그 파일 관리

---

# Phase 9: 시스템 안정성

**목표**: 24/7 안정적 운영

**예상 기간**: 3-4일

## 1. 에러 처리

### [MODIFY] [utils/error_handler.py](file:///e:/GitHub/UpbitTrader/utils/error_handler.py)

```python
import functools
import time

def retry_on_error(max_retries=3, delay=1):
    """에러 시 재시도 데코레이터"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max retries - 1:
                        raise
                    time.sleep(delay * (attempt + 1))
        return wrapper
    return decorator

class GlobalErrorHandler:
    """전역 에러 핸들러"""
    
    @staticmethod
    def handle_api_error(error):
        """API 에러 처리"""
        if "429" in str(error):
            # Rate Limit
            time.sleep(60)
        elif "401" in str(error):
            # 인증 에러
            raise Exception("API 키 확인 필요")
        # ... 기타 에러
```

## 2. 헬스 체크

### [NEW] [utils/health_checker.py](file:///e:/GitHub/UpbitTrader/utils/health_checker.py)

```python
class HealthChecker:
    """시스템 헬스 체크"""
    
    def check_api_connection(self):
        """API 연결 확인"""
        try:
            markets = self.api.get_markets()
            return len(markets) > 0
        except:
            return False
    
    def check_database(self):
        """DB 연결 확인"""
        try:
            self.db.execute("SELECT 1")
            return True
        except:
            return False
    
    def check_websocket(self):
        """WebSocket 연결 확인"""
        return self.ws.is_connected
    
    def run_health_check(self):
        """전체 헬스 체크"""
        results = {
            'api': self.check_api_connection(),
            'database': self.check_database(),
            'websocket': self.check_websocket()
        }
        
        if not all(results.values()):
            # 알림 발송
            pass
        
        return results
```

## 3. 메인 애플리케이션

### [NEW] [main.py](file:///e:/GitHub/UpbitTrader/main.py)

```python
import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow
from config import Config
from api.upbit_api import UpbitAPI
from database.db_manager import DatabaseManager
from utils.logger import setup_logger

def main():
    # 로거 초기화
    logger = setup_logger('main', 'logs/main.log')
    logger.info("🚀 Upbit Auto Trader 시작")
    
    # 설정 로드
    config = Config()
    config.validate()
    
    # API 초기화
    api = UpbitAPI(config.UPBIT_ACCESS_KEY, config.UPBIT_SECRET_KEY)
    
    # 데이터베이스 초기화
    db = DatabaseManager(config.DB_PATH)
    db.initialize_database()
    
    # GUI 시작
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"치명적 에러: {e}")
        raise
```

**검증 체크리스트**:
- [ ] 자동 재연결 동작
- [ ] 에러 복구 테스트
- [ ] 헬스 체크 동작
- [ ] 24시간 안정성 테스트
- [ ] 메모리 누수 확인

---

# 최종 통합 테스트

## 1. 기능 테스트
- [ ] API 연동
- [ ] 데이터 수집
- [ ] AI 예측
- [ ] 주문 실행
- [ ] 포지션 관리
- [ ] 백테스팅
- [ ] UI 동작
- [ ] 알림 발송

## 2. 성능 테스트
- [ ] 메모리 사용량
- [ ] CPU 사용률
- [ ] API 응답 시간
- [ ] 차트 렌더링 속도

## 3. 안정성 테스트
- [ ] 24시간 연속 운영
- [ ] 네트워크 장애 시나리오
- [ ] API 에러 처리
- [ ] 예외 상황 대응

## 4. 실전 테스트
- [ ] 페이퍼 트레이딩 2주
- [ ] 소액 실전 테스트 (10만원)
- [ ] 성과 모니터링
- [ ] 점진적 투자금 증액

---

# 배포 준비

## 1. 문서화
- `README.md`: 프로젝트 소개
- `INSTALL.md`: 설치 가이드
- `USER_MANUAL.md`: 사용자 매뉴얼
- `API_GUIDE.md`: API 문서
- `STRATEGY_GUIDE.md`: 전략 가이드

## 2. 패키징
```bash
# PyInstaller로 실행 파일 생성
pyinstaller --onefile --windowed main.py
```

## 3. 최종 체크리스트
- [ ] 모든 기능 테스트 통과
- [ ] 문서 작성 완료
- [ ] 보안 검토 (API 키 관리)
- [ ] 면책 조항 작성
- [ ] 라이선스 추가

---

> [!CAUTION]
> **면책 조항**
> 
> 본 프로그램은 교육 및 연구 목적으로 제작되었습니다.
> - 암호화폐 투자는 높은 위험을 동반합니다
> - 투자 손실에 대한 책임은 사용자에게 있습니다
> - 충분한 테스트 없이 실전 사용을 금지합니다
> - 소액부터 시작하여 점진적으로 투자금을 늘리세요

> [!TIP]
> **성공적인 운영을 위한 팁**
> 
> 1. 백테스팅을 충분히 수행하세요 (최소 6개월 이상 데이터)
> 2. 페이퍼 트레이딩으로 2주 이상 테스트하세요
> 3. 실전은 소액(10만원 이하)부터 시작하세요
> 4. 일일 손실 한도를 반드시 설정하세요
> 5. 정기적으로 AI 모델을 재학습하세요
> 6. 시장 상황 변화에 따라 전략을 조정하세요
