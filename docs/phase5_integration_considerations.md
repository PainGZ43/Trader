# Phase 5: 통합 (Integration) - 추가 고려사항 및 검토

## 1. 스레드 안전성 (Thread Safety) & 동시성 (Concurrency)
- **문제**: `EventBus`의 콜백은 백그라운드 스레드(또는 `asyncio` 루프)에서 실행될 수 있습니다. 반면, PyQt UI 업데이트는 반드시 **Main Thread**에서 이루어져야 합니다.
- **해결**:
    - `MainWindow`에 `pyqtSignal`을 정의하고, `EventBus` 구독 콜백에서 이 시그널을 `emit` 하도록 구현합니다.
    - `Qt.ConnectionType.QueuedConnection`을 활용하여 스레드 간 안전한 데이터 전달을 보장합니다.
    - `EventBus` 자체에 `publish_ui_event` 같은 헬퍼 메서드를 두어, UI 전용 이벤트를 명확히 구분하는 것도 방법입니다.

## 2. 데이터 일관성 (Data Consistency)
- **상태 동기화**: UI가 실행된 시점과 백엔드 데이터 수신 시점의 차이로 인해 초기 데이터가 비어있을 수 있습니다.
    - **해결**: UI 초기화 시 `request_initial_state` 이벤트를 발행하여, 백엔드가 현재 캐시된 데이터(최신 호가, 잔고 등)를 즉시 전송하도록 합니다.
- **주문 상태**: "주문 전송" -> "접수" -> "체결" 단계별 상태가 UI에 즉각 반영되어야 하며, 누락 시 사용자가 중복 주문을 낼 위험이 있습니다.
    - **해결**: 각 주문에 `UUID`를 부여하고, UI에서는 해당 주문 ID의 상태 변경 이벤트를 추적하여 버튼 활성/비활성 상태를 제어합니다.

## 3. 에러 처리 및 사용자 피드백 (Error Handling)
- **백엔드 에러 전파**: API 호출 실패나 네트워크 오류 발생 시, 로그에만 남기지 말고 UI에 명확히 알려야 합니다.
    - **해결**: `system.error` 토픽을 구독하여, 중요도(`CRITICAL`, `WARNING`)에 따라 `QMessageBox` 팝업이나 상태바 메시지로 표시합니다.
- **긴급 정지 피드백**: Panic Button을 눌렀을 때, 실제로 정지가 되었는지 확인하는 피드백 루프가 필요합니다.

## 4. 성능 최적화 (Performance)
- **이벤트 폭주 방지**: 틱 데이터나 호가 데이터는 초당 수십~수백 건 발생할 수 있습니다. 이를 그대로 UI에 쏘면 프리징이 발생합니다.
    - **해결**:
        - **Throttling**: `Dashboard`에 이미 구현된 `QTimer` 기반 업데이트 방식을 다른 패널(`ControlPanel`, `LogViewer`)에도 적용합니다.
        - **Data Batching**: 100ms 동안 쌓인 데이터를 리스트로 묶어서 한 번에 처리합니다.

## 5. 시작 및 종료 시퀀스 (Startup/Shutdown)
- **Graceful Shutdown**: 창을 닫을 때 백엔드 스레드/프로세스가 안전하게 종료되어야 합니다.
    - **해결**: `closeEvent`에서 `system.shutdown` 이벤트를 발행하고, 모든 백엔드 리소스(DB 연결, 소켓)가 정리될 때까지 잠시 대기(타임아웃 설정)합니다.

## 6. 운영 가시성 (Operational Visibility)
- **Latency Indicator**: 백엔드 데이터 생성 시각과 UI 수신 시각의 차이를 계산하여 "Data Delay: 50ms" 형태로 표시합니다.
- **Heartbeat Visualization**: 시스템/소켓의 Heartbeat 이벤트를 수신하여 상태바의 아이콘을 점멸(Blinking)시켜 연결 상태를 시각적으로 확신시켜 줍니다.

## 7. 시뮬레이션 제어 (Simulation Control)
- **Dry Run Toggle**: 설정 창이나 메인 툴바에 "Real Trading" <-> "Paper Trading" 전환 토글을 두어, 재시작 없이 모드를 변경할 수 있게 합니다.
- **Mock Data Injection**: 개발 및 테스트 용도로, 버튼 클릭 시 가상의 틱/호가 데이터를 주입하는 "Developer Mode" 기능을 숨겨둡니다.
