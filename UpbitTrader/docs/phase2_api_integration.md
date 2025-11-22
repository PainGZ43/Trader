# Phase 2: Upbit API 통합 상세 계획

**목표**: Upbit REST API 및 WebSocket API 완전 통합

**예상 기간**: 4-6일

---

## 1. Upbit API 이해

### 1.1 API 종류

**REST API**:
- 시장 정보 조회 (마켓 목록, 캔들, 호가, 체결)
- 계좌 정보 조회 (잔고, 주문 가능 금액)
- 주문 관리 (주문하기, 주문 조회, 주문 취소)
- API 키 필요 (계좌 관련 기능)

**WebSocket API**:
- 실시간 시세 (Ticker)
- 실시간 호가 (Orderbook)
- 실시간 체결 (Trade)
- API 키 불필요 (Public 데이터)

### 1.2 API 제한사항

> [!WARNING]
> Upbit API Rate Limiting:
> - REST API: 초당 10회, 분당 600회
> - 과도한 요청 시 429 에러 및 일시 차단
> - 요청 간격 관리 필수

---

## 2. REST API 구현

### 2.1 API 래퍼 클래스

#### [NEW] [api/upbit_api.py](file:///e:/GitHub/UpbitTrader/api/upbit_api.py)

**주요 기능**:

#### 2.1.1 초기화 및 인증
```python
import jwt
import hashlib
import uuid
from urllib.parse import urlencode
import requests

class UpbitAPI:
    """Upbit REST API 래퍼"""
    
    def __init__(self, access_key=None, secret_key=None):
        self.access_key = access_key
        self.secret_key = secret_key
        self.server_url = "https://api.upbit.com"
        
        # Rate Limiting
        self.last_request_time = 0
        self.request_interval = 0.1  # 100ms
        
    def _generate_auth_token(self, query=None):
        """JWT 토큰 생성"""
        payload = {
            'access_key': self.access_key,
            'nonce': str(uuid.uuid4()),
        }
        
        if query:
            query_string = urlencode(query).encode()
            m = hashlib.sha512()
            m.update(query_string)
            query_hash = m.hexdigest()
            payload['query_hash'] = query_hash
            payload['query_hash_alg'] = 'SHA512'
        
        jwt_token = jwt.encode(payload, self.secret_key)
        return f'Bearer {jwt_token}'
```

#### 2.1.2 시장 정보 조회

```python
def get_markets(self):
    """마켓 코드 조회"""
    url = f"{self.server_url}/v1/market/all"
    params = {'isDetails': 'true'}
    return self._request('GET', url, params=params)

def get_candles_minutes(self, market, unit=1, count=200):
    """분 캔들 조회 (1, 3, 5, 10, 15, 30, 60, 240)"""
    url = f"{self.server_url}/v1/candles/minutes/{unit}"
    params = {'market': market, 'count': count}
    return self._request('GET', url, params=params)

def get_candles_days(self, market, count=200):
    """일 캔들 조회"""
    url = f"{self.server_url}/v1/candles/days"
    params = {'market': market, 'count': count}
    return self._request('GET', url, params=params)

def get_ticker(self, markets):
    """현재가 정보 (Ticker)"""
    url = f"{self.server_url}/v1/ticker"
    params = {'markets': ','.join(markets) if isinstance(markets, list) else markets}
    return self._request('GET', url, params=params)

def get_orderbook(self, markets):
    """호가 정보"""
    url = f"{self.server_url}/v1/orderbook"
    params = {'markets': ','.join(markets) if isinstance(markets, list) else markets}
    return self._request('GET', url, params=params)

def get_trades_ticks(self, market, count=100):
    """최근 체결 내역"""
    url = f"{self.server_url}/v1/trades/ticks"
    params = {'market': market, 'count': count}
    return self._request('GET', url, params=params)
```

#### 2.1.3 계좌 정보 조회

```python
def get_accounts(self):
    """전체 계좌 조회"""
    url = f"{self.server_url}/v1/accounts"
    headers = {'Authorization': self._generate_auth_token()}
    return self._request('GET', url, headers=headers, auth_required=True)

def get_balance(self, currency='KRW'):
    """특정 통화 잔고 조회"""
    accounts = self.get_accounts()
    for account in accounts:
        if account['currency'] == currency:
            return float(account['balance'])
    return 0.0

def get_available_balance(self, currency='KRW'):
    """거래 가능 금액"""
    accounts = self.get_accounts()
    for account in accounts:
        if account['currency'] == currency:
            return float(account['balance']) - float(account['locked'])
    return 0.0
```

#### 2.1.4 주문 관리

```python
def order_limit_buy(self, market, price, volume):
    """지정가 매수"""
    query = {
        'market': market,
        'side': 'bid',
        'ord_type': 'limit',
        'price': str(price),
        'volume': str(volume)
    }
    return self._order(query)

def order_limit_sell(self, market, price, volume):
    """지정가 매도"""
    query = {
        'market': market,
        'side': 'ask',
        'ord_type': 'limit',
        'price': str(price),
        'volume': str(volume)
    }
    return self._order(query)

def order_market_buy(self, market, price):
    """시장가 매수 (금액 지정)"""
    query = {
        'market': market,
        'side': 'bid',
        'ord_type': 'price',
        'price': str(price)
    }
    return self._order(query)

def order_market_sell(self, market, volume):
    """시장가 매도 (수량 지정)"""
    query = {
        'market': market,
        'side': 'ask',
        'ord_type': 'market',
        'volume': str(volume)
    }
    return self._order(query)

def _order(self, query):
    """주문 실행"""
    url = f"{self.server_url}/v1/orders"
    headers = {'Authorization': self._generate_auth_token(query)}
    return self._request('POST', url, json=query, headers=headers, auth_required=True)

def get_order(self, uuid):
    """개별 주문 조회"""
    query = {'uuid': uuid}
    url = f"{self.server_url}/v1/order"
    headers = {'Authorization': self._generate_auth_token(query)}
    return self._request('GET', url, params=query, headers=headers, auth_required=True)

def get_orders(self, market=None, state='wait'):
    """주문 리스트 조회 (wait, done, cancel)"""
    query = {'state': state}
    if market:
        query['market'] = market
    
    url = f"{self.server_url}/v1/orders"
    headers = {'Authorization': self._generate_auth_token(query)}
    return self._request('GET', url, params=query, headers=headers, auth_required=True)

def cancel_order(self, uuid):
    """주문 취소"""
    query = {'uuid': uuid}
    url = f"{self.server_url}/v1/order"
    headers = {'Authorization': self._generate_auth_token(query)}
    return self._request('DELETE', url, params=query, headers=headers, auth_required=True)
```

#### 2.1.5 Rate Limiting 관리

```python
import time

def _rate_limit_wait(self):
    """요청 간격 제어"""
    current_time = time.time()
    time_since_last_request = current_time - self.last_request_time
    
    if time_since_last_request < self.request_interval:
        time.sleep(self.request_interval - time_since_last_request)
    
    self.last_request_time = time.time()

def _request(self, method, url, params=None, json=None, headers=None, auth_required=False):
    """HTTP 요청 공통 처리"""
    self._rate_limit_wait()
    
    try:
        if headers is None:
            headers = {}
        
        response = requests.request(
            method=method,
            url=url,
            params=params,
            json=json,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            # Too Many Requests
            raise Exception("API 요청 제한 초과. 잠시 후 다시 시도하세요.")
        else:
            error_msg = response.json().get('error', {})
            raise Exception(f"API 에러: {error_msg}")
            
    except requests.exceptions.Timeout:
        raise Exception("API 요청 시간 초과")
    except requests.exceptions.ConnectionError:
        raise Exception("네트워크 연결 에러")
    except Exception as e:
        raise e
```

---

## 3. WebSocket API 구현

### 3.1 WebSocket 연결 관리

#### [NEW] [api/upbit_websocket.py](file:///e:/GitHub/UpbitTrader/api/upbit_websocket.py)

**주요 기능**:

#### 3.1.1 초기화 및 연결

```python
import websocket
import json
import threading

class UpbitWebSocket:
    """Upbit WebSocket 클라이언트"""
    
    def __init__(self):
        self.ws_url = "wss://api.upbit.com/websocket/v1"
        self.ws = None
        self.is_connected = False
        self.callbacks = {
            'ticker': [],
            'orderbook': [],
            'trade': []
        }
        
    def connect(self):
        """WebSocket 연결"""
        websocket.enableTrace(False)
        self.ws = websocket.WebSocketApp(
            self.ws_url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )
        
        # 별도 스레드에서 실행
        wst = threading.Thread(target=self.ws.run_forever)
        wst.daemon = True
        wst.start()
```

#### 3.1.2 구독 관리

```python
def subscribe_ticker(self, markets, callback=None):
    """실시간 시세 구독"""
    subscribe_data = [
        {"ticket": "ticker"},
        {
            "type": "ticker",
            "codes": markets,
            "isOnlyRealtime": True
        }
    ]
    
    if callback:
        self.callbacks['ticker'].append(callback)
    
    self._send(subscribe_data)

def subscribe_orderbook(self, markets, callback=None):
    """실시간 호가 구독"""
    subscribe_data = [
        {"ticket": "orderbook"},
        {
            "type": "orderbook",
            "codes": markets,
            "isOnlyRealtime": True
        }
    ]
    
    if callback:
        self.callbacks['orderbook'].append(callback)
    
    self._send(subscribe_data)

def subscribe_trade(self, markets, callback=None):
    """실시간 체결 구독"""
    subscribe_data = [
        {"ticket": "trade"},
        {
            "type": "trade",
            "codes": markets,
            "isOnlyRealtime": True
        }
    ]
    
    if callback:
        self.callbacks['trade'].append(callback)
    
    self._send(subscribe_data)
```

#### 3.1.3 이벤트 핸들러

```python
def _on_open(self, ws):
    """연결 성공"""
    self.is_connected = True
    print("✅ WebSocket 연결 성공")

def _on_message(self, ws, message):
    """메시지 수신"""
    try:
        data = json.loads(message)
        msg_type = data.get('type')
        
        # 콜백 실행
        if msg_type in self.callbacks:
            for callback in self.callbacks[msg_type]:
                callback(data)
                
    except Exception as e:
        print(f"메시지 처리 에러: {e}")

def _on_error(self, ws, error):
    """에러 발생"""
    print(f"❌ WebSocket 에러: {error}")

def _on_close(self, ws, close_status_code, close_msg):
    """연결 종료"""
    self.is_connected = False
    print("⚠️ WebSocket 연결 종료")
    
    # 자동 재연결
    time.sleep(5)
    print("🔄 재연결 시도...")
    self.connect()

def _send(self, data):
    """데이터 전송"""
    if self.ws and self.is_connected:
        self.ws.send(json.dumps(data))
```

---

## 4. API 테스트

### 4.1 테스트 스크립트

#### [NEW] [tests/test_api.py](file:///e:/GitHub/UpbitTrader/tests/test_api.py)

```python
import pytest
from api.upbit_api import UpbitAPI
from api.upbit_websocket import UpbitWebSocket
import time

class TestUpbitAPI:
    """REST API 테스트"""
    
    @pytest.fixture
    def api(self):
        return UpbitAPI()
    
    def test_get_markets(self, api):
        """마켓 조회 테스트"""
        markets = api.get_markets()
        assert len(markets) > 0
        assert 'KRW-BTC' in [m['market'] for m in markets]
    
    def test_get_candles(self, api):
        """캔들 조회 테스트"""
        candles = api.get_candles_minutes('KRW-BTC', unit=1, count=10)
        assert len(candles) == 10
        assert 'opening_price' in candles[0]
    
    def test_get_ticker(self, api):
        """현재가 조회 테스트"""
        ticker = api.get_ticker(['KRW-BTC'])
        assert len(ticker) == 1
        assert ticker[0]['market'] == 'KRW-BTC'
    
    def test_get_orderbook(self, api):
        """호가 조회 테스트"""
        orderbook = api.get_orderbook(['KRW-BTC'])
        assert len(orderbook) > 0
        assert 'orderbook_units' in orderbook[0]

class TestUpbitWebSocket:
    """WebSocket 테스트"""
    
    def test_ticker_subscription(self):
        """실시간 시세 구독 테스트"""
        ws = UpbitWebSocket()
        received_data = []
        
        def on_ticker(data):
            received_data.append(data)
            print(f"Ticker: {data['code']} - {data['trade_price']}")
        
        ws.subscribe_ticker(['KRW-BTC'], callback=on_ticker)
        ws.connect()
        
        # 5초 대기
        time.sleep(5)
        
        assert len(received_data) > 0
```

### 4.2 간단한 테스트 스크립트

#### [NEW] [test_connection.py](file:///e:/GitHub/UpbitTrader/test_connection.py)

```python
"""API 연결 테스트"""
from api.upbit_api import UpbitAPI
from api.upbit_websocket import UpbitWebSocket
import time

def test_rest_api():
    print("=== REST API 테스트 ===")
    api = UpbitAPI()
    
    # 마켓 조회
    print("\n1. 마켓 조회")
    markets = api.get_markets()
    krw_markets = [m for m in markets if m['market'].startswith('KRW')]
    print(f"KRW 마켓 수: {len(krw_markets)}")
    
    # 현재가 조회
    print("\n2. BTC 현재가 조회")
    ticker = api.get_ticker(['KRW-BTC'])[0]
    print(f"BTC 가격: {ticker['trade_price']:,}원")
    
    # 캔들 조회
    print("\n3. 1분 캔들 조회")
    candles = api.get_candles_minutes('KRW-BTC', unit=1, count=5)
    for i, candle in enumerate(candles[:3]):
        print(f"{i+1}. 시가: {candle['opening_price']:,}, 종가: {candle['trade_price']:,}")
    
    print("\n✅ REST API 테스트 완료")

def test_websocket():
    print("\n=== WebSocket 테스트 ===")
    ws = UpbitWebSocket()
    
    def on_ticker(data):
        print(f"실시간 시세 - {data['code']}: {data['trade_price']:,}원")
    
    ws.subscribe_ticker(['KRW-BTC', 'KRW-ETH'], callback=on_ticker)
    ws.connect()
    
    print("10초간 실시간 데이터 수신...")
    time.sleep(10)
    
    print("\n✅ WebSocket 테스트 완료")

if __name__ == "__main__":
    test_rest_api()
    test_websocket()
```

---

## 5. API 유틸리티

### 5.1 헬퍼 함수

#### [NEW] [api/utils.py](file:///e:/GitHub/UpbitTrader/api/utils.py)

```python
"""API 유틸리티 함수"""

def format_currency(value):
    """통화 포맷팅"""
    return f"{value:,.0f}원"

def parse_market_code(market):
    """마켓 코드 파싱 (KRW-BTC -> BTC, KRW)"""
    parts = market.split('-')
    return parts[1], parts[0]

def calculate_fee(amount, fee_rate=0.0005):
    """수수료 계산 (기본 0.05%)"""
    return amount * fee_rate

def get_krw_markets_only(markets):
    """원화 마켓만 필터링"""
    return [m for m in markets if m['market'].startswith('KRW-')]

def candles_to_dataframe(candles):
    """캔들 데이터를 DataFrame으로 변환"""
    import pandas as pd
    
    df = pd.DataFrame(candles)
    df['timestamp'] = pd.to_datetime(df['candle_date_time_kst'])
    df = df.rename(columns={
        'opening_price': 'open',
        'high_price': 'high',
        'low_price': 'low',
        'trade_price': 'close',
        'candle_acc_trade_volume': 'volume'
    })
    df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    return df
```

---

## 검증 체크리스트

### ✅ REST API
- [ ] 마켓 조회 성공
- [ ] 캔들 데이터 조회 (1분, 5분, 일봉)
- [ ] 현재가 조회
- [ ] 호가 조회
- [ ] 체결 내역 조회
- [ ] Rate Limiting 동작 확인

### ✅ REST API (인증 필요)
- [ ] API 키 설정 완료
- [ ] 계좌 조회 성공
- [ ] 잔고 조회
- [ ] 주문 내역 조회
- [ ] 테스트 주문 (소액)
- [ ] 주문 취소

### ✅ WebSocket
- [ ] 연결 성공
- [ ] 실시간 시세 수신
- [ ] 실시간 호가 수신
- [ ] 실시간 체결 수신
- [ ] 재연결 로직 동작
- [ ] 다중 마켓 구독

### ✅ 에러 처리
- [ ] 네트워크 에러 처리
- [ ] API 제한 에러 처리
- [ ] 인증 에러 처리
- [ ] 타임아웃 처리

---

## 다음 단계

Phase 2 완료 후:
- ✅ Phase 3: 데이터 수집 및 처리 시작
- 📊 OHLCV 데이터 수집 자동화
- 📈 기술적 지표 계산

> [!CAUTION]
> 실제 거래 전 반드시 소액으로 API 테스트를 진행하세요. API 키는 출금 권한을 제거한 상태로 사용하는 것을 권장합니다.

> [!TIP]
> WebSocket은 실시간 데이터 수신에 필수적입니다. 안정적인 재연결 로직을 구현하여 24/7 운영 시 연결이 끊기지 않도록 하세요.
