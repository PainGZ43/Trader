# 전략 관리 개선 계획

## 목표 설명
전략의 동적 로딩, 파라미터 스키마 자동 생성, 그리고 설정을 위한 더욱 강력한 UI를 지원하도록 전략 관리 시스템을 개선합니다.

## 사용자 검토 필요 사항
> [!NOTE]
> 이 작업은 전략이 등록되는 방식을 리팩토링합니다. UI의 기존 하드코딩된 목록은 동적 검색으로 대체됩니다.

## 변경 제안

### 전략 코어 (Strategy Core)
#### [MODIFY] [strategy/base_strategy.py](file:///e:/GitHub/Trader/PainTrader/strategy/base_strategy.py)
- 모든 전략에 대해 `get_parameter_schema`가 추상 메서드이거나 잘 정의되어 있는지 확인합니다.
- UI 표시를 위한 `get_name` 및 `get_description` 메서드를 추가합니다.

#### [MODIFY] [strategy/strategies.py](file:///e:/GitHub/Trader/PainTrader/strategy/strategies.py)
- 모든 내장 전략(`VolatilityBreakout`, `RSI` 등)에 대해 `get_parameter_schema`를 구현합니다.

#### [NEW] [strategy/registry.py](file:///e:/GitHub/Trader/PainTrader/strategy/registry.py)
- `StrategyRegistry` 클래스를 생성하여 다음을 수행합니다:
    - 전략 클래스 검색 (`inspect` 또는 수동 등록 사용).
    - 사용 가능한 전략 목록 제공.
    - 설정(config)을 사용하여 전략 인스턴스화.

### UI
#### [MODIFY] [ui/widgets/settings_tabs.py](file:///e:/GitHub/Trader/PainTrader/ui/widgets/settings_tabs.py)
- `StrategyRegistry`를 사용하도록 `StrategySettingsTab`을 업데이트합니다.
- 하드코딩된 전략 목록을 제거합니다.
- `get_parameter_schema`를 기반으로 파라미터 입력 폼을 동적으로 생성합니다.

## 검증 계획

### 자동화 테스트
- **테스트 1**: 레지스트리 검색
    - `StrategyRegistry`가 모든 내장 전략을 찾는지 확인합니다.
- **테스트 2**: 스키마 유효성 검사
    - 모든 전략이 유효한 파라미터 스키마를 반환하는지 확인합니다.

### 수동 검증
- 설정 다이얼로그 -> 전략 탭을 엽니다.
- 모든 전략이 목록에 표시되는지 확인합니다.
- 파라미터를 변경하면 `config`가 업데이트되는지 확인합니다.
