# Phase 4: 설정 및 관리 (Settings & Management) 상세 설계

## 1. 목표
사용자가 시스템의 핵심 동작(API 연결, 전략 파라미터, 리스크 관리)을 직관적으로 제어할 수 있는 통합 설정 환경을 구축합니다. 특히, 전략 파라미터를 코드 수정 없이 UI에서 튜닝할 수 있는 유연성을 확보하는 것이 핵심입니다.

## 2. 아키텍처 설계

### 2.1 Unified Settings Dialog (통합 설정 창)
기존의 파편화된 설정 창(`SettingsDialog`, `KeySettingsDialog`)을 하나의 `QDialog` 내 `QTabWidget`으로 통합합니다.

#### 클래스 구조
```python
class SettingsDialog(QDialog):
    def __init__(self):
        self.tabs = QTabWidget()
        self.tab_account = AccountSettingsTab()  # 기존 KeySettingsDialog 기능
        self.tab_strategy = StrategySettingsTab() # 신규: 전략 파라미터 튜닝
        self.tab_risk = RiskSettingsTab()         # 신규: 리스크/알림 설정
        self.tab_system = SystemSettingsTab()     # 신규: 시스템/로그 설정
```

### 2.2 데이터 흐름 (Data Flow)
1.  **Load**: 다이얼로그 오픈 시 `ConfigLoader`와 `SecureStorage`에서 현재 설정값을 로드하여 UI에 반영.
2.  **Edit**: 사용자가 값 수정 (메모리 상에서만 변경).
3.  **Apply/Save**: "저장" 버튼 클릭 시, 변경된 값을 파일(`config.yaml`) 및 DB(`trade.db`)에 영구 저장하고, `EventBus`를 통해 실행 중인 모듈(Strategy, RiskManager 등)에 실시간 전파.

---

## 3. 탭별 상세 설계

### Tab 1: 계정 및 API (Accounts & API)
- **기능**: 키움 API 키 등록/검증/삭제, 모의/실전 투자 전환.
- **UI 구성**: 기존 `KeySettingsDialog`의 테이블 및 등록 폼을 그대로 이식하되, 레이아웃을 최적화.
- **개선점**: "자동 로그인" 옵션을 이 탭 상단으로 이동하여 접근성 강화.

### Tab 2: 전략 설정 (Strategy Tuning)
- **기능**: 활성 전략 선택 및 전략별 파라미터 동적 편집.
- **UI 구성**:
    - **좌측**: 전략 목록 (ListWidget)
    - **우측**: 선택된 전략의 파라미터 편집 테이블 (Property Grid)
- **동적 파라미터 로직**:
    - 각 전략 클래스에 `get_parameter_schema()` 정적 메서드 추가.
    - 스키마 예시:
      ```python
      {
          "rsi_period": {"type": "int", "min": 5, "max": 30, "default": 14, "desc": "RSI 계산 기간"},
          "buy_threshold": {"type": "float", "min": 0.0, "max": 100.0, "default": 30.0},
          "ma_type": {"type": "enum", "options": ["SMA", "EMA"], "default": "SMA"}
      }
      ```
    - UI는 이 스키마를 읽어 적절한 입력 위젯(SpinBox, ComboBox 등)을 자동 생성.

### Tab 3: 리스크 및 알림 (Risk & Notification)
- **리스크 관리**:
    - **Max Daily Loss**: 일일 최대 손실 한도 (도달 시 자동 매매 정지).
    - **Max Position Size**: 종목당 최대 투입 금액 (예수금 대비 %).
- **알림 설정**:
    - **KakaoTalk Token**: 토큰 입력 및 "테스트 발송" 버튼.
    - **알림 조건**: 체결 시, 에러 발생 시, 장 마감 리포트 등 체크박스로 선택.

### Tab 4: 시스템 (System)
- **로그 설정**: 로그 레벨(DEBUG/INFO/ERROR), 보관 기간 설정.
- **데이터베이스**: DB 파일 용량 표시 및 "최적화(Vacuum)" 버튼.
- **초기화**: "모든 설정 초기화" (Factory Reset) 버튼 (붉은색 경고).

---

## 4. 로그 뷰어 고도화 (`LogViewer`)
메인 윈도우 하단에 도킹된 로그 뷰어의 기능을 강화합니다.

- **검색 바**: 로그 메시지 내 키워드 검색 (하이라이트).
- **필터링**: 레벨별(INFO, ERROR) 필터 콤보박스.
- **Auto Scroll**: 최신 로그 자동 추적 On/Off 토글.
- **Export**: `Save as...` 버튼으로 현재 로그를 텍스트 파일로 저장.

## 5. 구현 로드맵
1.  **Step 1 (Core)**: `BaseStrategy`에 파라미터 스키마 인터페이스 정의.
2.  **Step 2 (UI)**: `SettingsDialog` 뼈대 및 탭 구조 구현.
3.  **Step 3 (Migration)**: `KeySettingsDialog` 로직 이식.
4.  **Step 4 (Dynamic UI)**: 전략 파라미터 동적 생성 로직 구현.
5.  **Step 5 (Integration)**: 설정 변경 시 `EventBus` 이벤트 발행 및 핸들링.
