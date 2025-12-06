# 전략 상태 복구 구현 계획

## 목표 설명
봇이 충돌하거나 재시작된 후에도 전략의 상태(현재 포지션, 평균 진입가, 누적 수익 등)를 복구할 수 있도록 합니다. 현재 `OrderManager`는 활성 주문을 복구하지만, `ExecutionEngine`은 전략 상태를 복구하지 않습니다.

## 사용자 검토 필요 사항
> [!IMPORTANT]
> 이 변경 사항은 `ExecutionEngine`이 모든 거래 실행 시 데이터베이스와 상호 작용하도록 수정합니다. 이는 약간의 지연(DB 쓰기)을 추가하지만 데이터 안전성을 보장합니다.

## 변경 제안

### 실행 계층 (Execution Layer)
#### [MODIFY] [engine.py](file:///e:/GitHub/Trader/PainTrader/execution/engine.py)
- `__init__` 또는 `initialize`에서 `StrategyStateDAO`를 초기화합니다.
- `register_strategy`에서 `StrategyStateDAO.load_state`를 사용하여 기존 상태 로드를 시도합니다.
- 상태가 발견되면 `strategy.set_state`를 사용하여 복구합니다.
- `ExecutionEngine`이 `EventBus`의 `order.filled` 이벤트를 구독하도록 설정합니다.
- `on_order_filled` 핸들러를 구현하여:
    - 관련 전략을 식별합니다.
    - `strategy.update_position`을 호출합니다.
    - `dao.save_state`를 호출하여 상태를 저장합니다.

#### [MODIFY] [order_manager.py](file:///e:/GitHub/Trader/PainTrader/execution/order_manager.py)
- `event_bus`를 임포트합니다.
- `on_order_event` (체결 시)에서 세부 정보와 함께 `order.filled` 이벤트를 발행합니다.

#### [MODIFY] [base_strategy.py](file:///e:/GitHub/Trader/PainTrader/strategy/base_strategy.py)
- `update_position` 로직이 정확한지 확인합니다.

## 검증 계획

### 자동화 테스트
- 새 테스트 파일 `tests/test_recovery.py` 생성.
- **테스트 1**: 전략 상태 지속성 시뮬레이션.
    - 전략을 생성하고 상태를 설정합니다(예: 포지션=10).
    - DAO를 통해 DB에 저장합니다.
    - 새 엔진을 생성하고 전략을 등록합니다.
    - 전략의 포지션이 10인지 확인합니다.
- **테스트 2**: 주문 체결 및 상태 업데이트 시뮬레이션.
    - `OrderManager`가 이벤트를 발행하도록 모의(Mock)합니다.
    - 엔진이 전략 상태를 업데이트하고 DB에 저장하는지 확인합니다.

### 수동 검증
- 봇을 실행합니다.
- 거래가 발생할 때까지 기다리거나 강제로 발생시킵니다.
- 봇을 중지합니다.
- 봇을 재시작합니다.
- 로그에서 "State restored" 메시지를 확인합니다.
