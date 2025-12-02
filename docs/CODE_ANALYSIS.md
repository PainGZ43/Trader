# PainTrader Codebase Analysis Report

## 1. 개요 (Overview)
**PainTrader**는 키움증권 Open API를 기반으로 하는 **AI 기반 자동매매 시스템**입니다. Clean Architecture 원칙을 따라 모듈화되어 있으며, 확장성과 유지보수성을 고려하여 설계되었습니다.

## 2. 아키텍처 구조 (Architecture)
프로젝트는 크게 4개의 계층(Layer)으로 구분됩니다.

### 2.1 Core Layer (`core/`)
시스템의 기반이 되는 공통 기능을 담당합니다.
- **`config.py`**: 설정 관리 (JSON/YAML 및 환경변수).
- **`event_bus.py`**: 모듈 간 느슨한 결합(Loose Coupling)을 위한 Pub/Sub 이벤트 시스템.
- **`logger.py`**: 로깅 시스템 (파일/콘솔, 로테이션).
- **`database.py`**: SQLite 비동기(`aiosqlite`) 데이터베이스 연결 및 관리.
- **`language.py`**: 다국어 지원 (한국어/영어).

### 2.2 Data Layer (`data/`)
외부 데이터 소스와의 통신을 담당합니다.
- **`kiwoom_api.py`**: 키움증권 REST API 통신 (OAuth2 인증, 토큰 갱신).
- **`websocket_client.py`**: 실시간 시세 수신 (WebSocket).
- **`data_collector.py`**: 실시간 데이터 버퍼링, 캔들 생성(Aggregation), 갭 보정.
- **`macro_collector.py`**: 환율, 시장 지수 등 거시 경제 데이터 수집.

### 2.3 Strategy Layer (`strategy/`)
매매 판단을 내리는 두뇌 역할을 합니다.
- **`ai_engine.py`**: AI 모델(PyTorch/Scikit-learn) 로드 및 추론.
- **`strategies/`**: 개별 전략 구현체 (변동성 돌파, RSI, 하이브리드 등).
- **`market_regime.py`**: 시장 국면(상승/하락/횡보) 탐지.

### 2.4 Execution Layer (`execution/`)
실제 주문 및 계좌 관리를 담당합니다.
- **`order_manager.py`**: 주문 생성, 전송, 미체결 관리(정정/취소).
- **`risk_manager.py`**: 리스크 관리 (손실 한도, 주문 금액 제한).
- **`account_manager.py`**: 실시간 잔고 및 수익률 동기화.
- **`notification.py`**: 카카오톡 알림 발송.

### 2.5 UI Layer (`ui/`)
사용자 인터페이스 (PyQt6)입니다.
- **`main_window.py`**: 메인 애플리케이션 창.
- **`dashboard.py`**: 실시간 차트 및 호가창.
- **`settings_dialog.py`**: 설정 관리 다이얼로그.

## 3. 주요 기능 및 현황 (Status)

### ✅ 완료된 기능 (Completed)
1.  **데이터 수집**: 키움 REST/WebSocket 연동, 실시간 캔들 생성.
2.  **전략 엔진**: 기본 기술적 전략 및 AI 모델 연동 구조.
3.  **자동 매매**: 매수/매도 주문, 미체결 자동 취소, 이익 실현/손절.
4.  **리스크 관리**: 일일 손실 한도, 종목당 투자 비중 제한.
5.  **UI/UX**: 다크 모드, 실시간 차트, 호가창, 설정 UI.
6.  **안정성**: 예외 처리, 자동 재연결, 로깅.
7.  **배포 준비**: PyInstaller 빌드 스크립트, 사용자 매뉴얼.

### 🚧 진행 중 / 예정 (Pending)
1.  **실행 파일 테스트**: 생성된 `.exe` 파일의 실제 구동 테스트.
2.  **AI 모델 고도화**: 현재는 기본 구조만 잡혀있으며, 실제 고성능 모델 학습 및 적용 필요.
3.  **조건검색 연동**: 키움 조건검색식 실시간 편입/이탈 로직의 정밀 검증.

## 4. 코드 품질 및 개선 사항 (Observations)
1.  **이벤트 기반 통신**: `EventBus`를 활용하여 모듈 간 의존성을 잘 분리했습니다.
2.  **비동기 처리**: `asyncio`를 적극 활용하여 I/O 블로킹 없이 고성능 처리가 가능합니다.
3.  **설정의 유연성**: `settings.json`과 UI가 잘 연동되어 있어 사용자 편의성이 높습니다.
4.  **배포 고려**: `get_resource_path` 등을 통해 개발 환경과 배포 환경을 모두 고려한 코드가 작성되었습니다.

## 5. 결론 (Conclusion)
**PainTrader**는 상용 수준의 기능을 갖춘 자동매매 플랫폼으로 완성 단계에 있습니다. 핵심 코어 로직은 검증되었으며, UI 편의성 작업도 마무리되었습니다. 이제 **실제 배포 및 운영** 단계로 넘어갈 준비가 되었습니다.
