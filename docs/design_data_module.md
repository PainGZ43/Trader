# 상세 설계: 데이터 수집 및 처리 모듈 (키움 공식 REST API 전용)

## 1. 개요
이 모듈은 **키움증권 공식 REST API**를 사용하여 데이터를 수집합니다. 별도의 Bridge 서버 없이 64-bit 환경에서 직접 통신하며, OAuth2 인증 방식을 따릅니다.

## 2. 핵심 컴포넌트

### 2.1. Kiwoom REST Client
공식 API 엔드포인트와 통신하는 클라이언트입니다.

*   **역할**:
    *   **인증 (Auth)**: API Key/Secret을 사용해 Access Token 발급 및 갱신 (자동 관리).
    *   **HTTP 요청**: 주문, 잔고, 차트 데이터 조회.
    *   **WebSocket 연결**: 실시간 시세 수신.
    *   **제한 관리**: 초당 요청 횟수 제한 준수.

*   **주요 메서드**:
    *   `get_token()`: 토큰 발급/갱신.
    *   `get_ohlcv(symbol, interval)`: 과거 데이터 조회.
    *   `send_order(...)`: 주문 전송.

### 2.2. Data Collector (수집기)
*   **실시간 수집 (WebSocket)**:
    *   공식 WS 주소로 접속하여 JSON 데이터 수신.
    *   `ping/pong` 유지 및 재연결 로직 내장.
*   **과거 데이터 수집 (REST)**:
    *   초기 데이터 로딩 시 REST API 활용.
*   **거시 데이터 수집 (Macro)**:
    *   **시장 지수**: 업종차트조회(opt20006) 등을 통해 코스피/코스닥 지수 수집.
    *   **환율**: 외부 API (예: Yahoo Finance) 또는 키움 해외선물 API 활용.

### 2.3. Data Manager (데이터 관리자)
*   **메모리 캐시**: DataFrame으로 관리.
*   **DB 저장**: SQLite 비동기 저장.
    *   **Bulk Insert**: 대량 데이터(Gap Filling, 종목 코드) 처리 시 `executemany` 사용하여 성능 최적화.
    *   **Schema Versioning**: `schema_version` 테이블을 통해 DB 스키마 변경 이력 관리 및 자동 마이그레이션 지원.
*   **지표 계산**: TA-Lib 활용.

## 3. 데이터베이스 스키마 (SQLite)

### 3.1. `market_data` (분봉/일봉 데이터)
| 컬럼명 | 타입 | 설명 |
| :--- | :--- | :--- |
| `timestamp` | DATETIME | 캔들 시작 시간 (PK) |
| `symbol` | TEXT | 종목 코드 (예: 005930) (PK) |
| `interval` | TEXT | 분봉 단위 (예: 1m, 5m, 1d) (PK) |
| `open` | INTEGER | 시가 (주식은 정수) |
| `high` | INTEGER | 고가 |
| `low` | INTEGER | 저가 |
| `close` | INTEGER | 종가 |
| `volume` | INTEGER | 거래량 |

### 3.2. `trade_history` (매매 기록)
| 컬럼명 | 타입 | 설명 |
| :--- | :--- | :--- |
| `id` | INTEGER | Auto Increment (PK) |
| `timestamp` | DATETIME | 체결 시간 |
| `symbol` | TEXT | 종목 코드 |
| `side` | TEXT | 매수/매도 (BUY/SELL) |
| `price` | INTEGER | 체결 가격 |
| `quantity` | INTEGER | 체결 수량 |
| `strategy` | TEXT | 사용된 전략 이름 |
| `profit` | INTEGER | 실현 손익 (매도 시) |
| `profit_rate` | REAL | 수익률 (%) |

### 3.3. `schema_version` (스키마 버전 관리)
| 컬럼명 | 타입 | 설명 |
| :--- | :--- | :--- |
| `version` | INTEGER | DB 스키마 버전 (PK) |
| `updated_at` | DATETIME | 업데이트 일시 |

## 5. 데이터 계층 심화 고려사항 (Advanced Considerations)

### 5.1. 정교한 속도 제한 (Rate Limiting)
*   **이슈**: 키움 REST API는 초당/분당 요청 제한이 엄격할 수 있습니다 (예: 초당 5회). 위반 시 계정 차단 위험.
*   **해결**: **Token Bucket 알고리즘**을 구현한 `RateLimiter` 클래스 사용.
    *   모든 REST 요청은 `RateLimiter.acquire()`를 통과해야만 전송.
    *   우선순위 큐(Priority Queue)를 도입하여 '주문' 요청을 '조회' 요청보다 먼저 처리.

### 5.2. 데이터 결손 보정 (Gap Filling)
*   **이슈**: 네트워크 불안정으로 WebSocket이 잠시 끊겼다가 재연결되면 그 사이의 데이터가 누락됨.
*   **해결**:
    *   재연결 직후, 마지막 수신 시간(Last Timestamp)부터 현재까지의 데이터를 REST API로 조회하여 채워넣는 로직 구현.
    *   `Data Manager`가 데이터의 연속성을 주기적으로 검사.

### 5.3. 장 운영 시간 관리 (Market Hours)
*   **이슈**: 주식 시장은 09:00 ~ 15:30에만 열림. 장전/장후 시간외 거래 데이터 처리 여부.
*   **해결**:
    *   `MarketSchedule` 모듈을 두어 장 시작/마감 이벤트를 발행.
    *   장 마감 후에는 불필요한 API 폴링을 중단하여 리소스 절약.
    *   매일 아침 장 시작 전(08:30)에 종목 마스터(상장/폐지 정보) 동기화.

### 5.4. 종목 마스터 동기화 (Symbol Master)
*   **이슈**: 신규 상장, 상장 폐지, 거래 정지 종목이 매일 바뀜.
*   **해결**:
    *   **매일 아침 `GetCodeListByMarket` API를 호출하여 종목 리스트 DB 업데이트.**
    *   관리종목, 거래정지 종목은 매매 대상에서 자동 제외 필터링.

## 6. 테스트 계획 (Testing Plan)

### 6.1. 단위 테스트 (Unit Test)
*   **인증 테스트**: Mock 서버를 사용하여 토큰 발급 및 갱신 로직 검증.
*   **파싱 테스트**: JSON 응답 데이터가 DataFrame으로 정확히 변환되는지 검증.
*   **속도 제한 테스트**: `RateLimiter`가 설정된 초당 요청 수를 초과하지 않는지 검증.

### 6.2. 통합 테스트 (Integration Test)
*   **실제 API 연결**: (장 운영 시간 외) 로그인 및 단순 조회(현재가) 성공 여부 확인.
*   **WebSocket 안정성**: 1시간 이상 연결 유지 시 끊김 없는지, Ping/Pong 로그 확인.
*   **DB 저장**: 수신된 데이터가 SQLite에 누락 없이 저장되는지 확인.
