# Phase 4: 설정 및 관리 (Settings & Management) 구현 검토 및 고려사항

## 1. 개요
Phase 3(제어 및 실행)까지 완료되어 트레이딩의 핵심 기능은 갖춰졌습니다. Phase 4에서는 시스템의 **설정 관리**, **전략 파라미터 튜닝**, **리스크 관리**, 그리고 **시스템 모니터링** 기능을 구현하여 사용성을 완성합니다.

## 2. 현황 분석
- **SettingsDialog (`ui/settings_dialog.py`)**: 초기 개발용 단순 입력 폼. `KeySettingsDialog`와 중복되거나 기능이 부족함.
- **KeySettingsDialog (`ui/key_settings_dialog.py`)**: 멀티 계좌 및 키 관리가 잘 구현되어 있음. 이를 메인 설정의 일부로 통합하거나 연동해야 함.
- **LogViewer (`ui/log_viewer.py`)**: 기본적인 로그 수집 및 색상 표시 기능 구현됨. 필터링 기능 보강 필요.

## 3. 상세 고려사항 및 제안

### 3.1 설정 다이얼로그 통합 (Unified Settings)
- **구조**: `QTabWidget`을 사용하여 카테고리별로 설정을 분리합니다.
    - **Tab 1: API & Accounts**: 기존 `KeySettingsDialog`의 기능을 이 탭으로 이식하거나, 버튼을 통해 호출하도록 구성.
    - **Tab 2: Strategy (전략)**:
        - 전략별 파라미터(예: RSI 기간, 이평선 종류 등)를 테이블 형태로 편집.
        - `PropertyGrid` 형태의 UI를 도입하여 직관적인 값 수정 지원.
    - **Tab 3: Risk & Notification**:
        - 손실 한도(Stop Loss), 목표 수익(Take Profit) 설정.
        - 카카오톡 토큰 설정 및 테스트 발송 기능.

### 3.2 시스템 모니터링 (System Health)
- **SystemHealth 탭**:
    - CPU, Memory 사용량을 실시간 그래프로 표시 (PyQtGraph 재사용).
    - API 호출 횟수 및 남은 요청 수(Rate Limit) 시각화.
    - 네트워크 지연 시간(Ping) 표시.

### 3.3 로그 뷰어 고도화
- **검색 기능**: 텍스트 검색 필드 추가.
- **Auto-Scroll 제어**: 로그를 읽을 때 스크롤이 튀지 않도록 "Auto Scroll" 체크박스 추가.
- **파일 저장**: 현재 로그를 별도 파일로 내보내는 기능.

## 4. 기술적 구현 전략
- **Config Persistence**: 모든 설정 변경 사항은 `config.yaml` 또는 `secure_storage`에 즉시 저장되어야 하며, 프로그램 재시작 시 복원되어야 합니다.
- **Dynamic Strategy Params**: 전략 클래스에서 `get_parameters()` 메서드를 통해 메타데이터를 제공받아, 설정 UI를 동적으로 생성하는 구조를 제안합니다. (하드코딩 방지)

## 5. 추천 로드맵
1.  **Step 1**: `SettingsDialog` 전면 개편 (탭 구조 도입)
2.  **Step 2**: `KeySettingsDialog` 기능을 `SettingsDialog`의 첫 번째 탭으로 통합
3.  **Step 3**: 전략 파라미터 편집 UI 구현 (동적 생성 로직)
4.  **Step 4**: `LogViewer` 기능 보강 및 메인 윈도우 하단 패널 연동
