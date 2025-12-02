# 상세 설계: 관심종목(Watchlist) 및 차트 보조지표(Chart Indicators) 강화

## 1. 개요
사용자의 매매 편의성을 높이기 위해 **관심종목 관리 기능**을 체계화하고, **차트 보조지표**를 자유롭게 설정할 수 있는 기능을 구현한다.

---

## 2. 관심종목 (Watchlist) 기능 강화

### 2.1 목표
- 사용자가 여러 개의 **관심 그룹**을 생성하고 관리할 수 있어야 한다.
- 각 그룹에 종목을 자유롭게 **추가/삭제**할 수 있어야 한다.
- 관심종목의 **실시간 시세(현재가, 등락률, 거래량)**를 한눈에 확인할 수 있어야 한다.
- 프로그램 재시작 시에도 설정이 **유지(Persistence)**되어야 한다.

### 2.2 데이터 구조 (Settings)
`settings.json` 내에 다음과 같은 구조로 저장한다.
```json
{
  "watchlist": {
    "groups": [
      {
        "id": "group_1",
        "name": "기본 관심그룹",
        "codes": ["005930", "000660", "035420"]
      },
      {
        "id": "group_2",
        "name": "AI 반도체",
        "codes": ["042700", "000270"]
      }
    ],
    "active_group_id": "group_1"
  }
}
```

### 2.3 UI 설계 (WatchlistWidget)
`ControlPanel` 또는 별도의 Dock Widget으로 배치한다.

1.  **상단 툴바 (Group Controls)**
    *   **그룹 선택 (ComboBox)**: 현재 활성화된 그룹 선택
    *   **그룹 관리 (Button)**: 그룹 추가/이름 변경/삭제 다이얼로그 호출
    *   **종목 추가 (Search Bar)**: 종목명/코드 검색 -> 엔터 시 현재 그룹에 추가

2.  **종목 리스트 (TableWidget)**
    *   **컬럼**: 종목명, 현재가, 등락률(Color), 거래량
    *   **인터랙션**:
        *   **클릭**: 차트 및 호가창을 해당 종목으로 변경 (`EventBus` 발행)
        *   **우클릭 메뉴**: "그룹에서 삭제", "매수 주문 창으로 이동"
        *   **드래그 앤 드롭**: 종목 순서 변경 (필수 구현)

### 2.4 구현 로직
1.  **초기화**: `ConfigLoader`에서 watchlist 데이터 로드.
2.  **데이터 수집**: 활성 그룹의 모든 종목에 대해 `DataCollector` 또는 `WebSocketClient`를 통해 실시간 시세 구독.
    *   *주의*: Kiwoom API의 실시간 등록 개수 제한(약 100개)을 고려하여, 활성 그룹 종목만 구독하고 비활성 그룹은 구독 해지하는 로직 필요.
3.  **이벤트 처리**:
    *   `market.data.realtime`: 수신된 데이터로 테이블 행 업데이트.
    *   `watchlist.changed`: 그룹 변경 시 구독 목록 갱신.

---

## 3. 차트 보조지표 (Chart Indicators) 강화

### 3.1 목표
- 사용자가 원하는 **보조지표를 선택하여 차트에 추가**할 수 있어야 한다.
- 각 지표의 **파라미터(기간, 색상 등)를 설정**할 수 있어야 한다.
- **오버레이(Overlay)** 지표(이평선, 볼린저밴드)와 **서브차트(Sub-chart)** 지표(RSI, MACD, 거래량)를 구분하여 렌더링한다.

### 3.2 지원 지표 목록
1.  **Overlay (메인 차트 위)**
    *   이동평균선 (SMA/EMA): 기간 설정 (5, 20, 60, 120 등)
    *   볼린저 밴드 (Bollinger Bands): 기간, 승수(std dev)
    *   일목균형표 (Ichimoku): (추후 고려)
2.  **Sub-chart (하단 별도 영역)**
    *   거래량 (Volume): 기본 표시
    *   RSI (Relative Strength Index): 기간, 과매수/과매도 기준선
    *   MACD: Fast, Slow, Signal 기간
    *   Stochastic: K, D 기간

### 3.3 UI 설계 (ChartWidget 확장)
1.  **지표 설정 메뉴 (Toolbar/Menu)**
    *   차트 상단에 "지표(Indicators)" 버튼 추가.
    *   클릭 시 체크박스가 있는 메뉴 또는 설정 다이얼로그 표시.

2.  **지표 설정 다이얼로그**
    *   **좌측**: 지표 목록 리스트
    *   **우측**: 선택된 지표의 파라미터(기간, 색상) 입력 폼
    *   **적용**: 변경 사항 즉시 반영

3.  **차트 레이아웃 (PyQtGraph)**
    *   `GraphicsLayoutWidget` 활용.
    *   **Row 0**: 메인 가격 차트 (Candle + Overlay)
    *   **Row 1**: 거래량 차트 (기본)
    *   **Row 2~N**: 추가된 서브차트 (RSI, MACD 등 동적 추가/제거)

### 3.4 데이터 처리 (IndicatorEngine)
1.  **계산 요청**: 차트 업데이트 시(`update_chart`), 활성화된 지표 목록을 확인.
2.  **TA-Lib 연동**: `IndicatorEngine`에 필요한 지표 계산 메서드 호출 (이미 대부분 구현됨).
3.  **캐싱**: 매 틱마다 전체 과거 데이터를 재계산하면 느리므로, 1분봉 완성 시점에만 전체 재계산하거나, 최신 값만 업데이트하는 최적화 고려. (일단은 매 업데이트 시 계산하되, 데이터 길이를 1000개 정도로 제한하여 성능 확보)

---

## 4. 추가 검토 및 보완 사항 (Refinements)

### 4.1 관심종목 (Watchlist)
1.  **API 제한 관리 (Pagination/Limits)**
    *   Kiwoom API는 실시간 등록 종목 수에 제한(약 100개)이 있음.
    *   **해결책**: 한 그룹당 최대 등록 개수를 100개로 제한하거나, 100개가 넘을 경우 '페이지' 개념을 도입하여 현재 보고 있는 페이지의 종목만 실시간 구독하도록 구현.
2.  **드래그 앤 드롭 (Reordering)**
    *   사용자 경험(UX)을 위해 종목 간 순서 변경은 필수적임. `QListWidget` 또는 `QTableWidget`의 Drag & Drop 모드를 활성화하여 구현.
3.  **가져오기/내보내기 (Import/Export)**
    *   백업 및 공유를 위해 CSV 또는 JSON 파일로 관심종목 리스트를 내보내고 가져오는 기능 추가 고려.

### 4.2 차트 보조지표 (Chart)
1.  **지표 템플릿 (Templates)**
    *   사용자가 선호하는 지표 조합(예: "추세 매매용", "단타용")을 '템플릿'으로 저장하고 불러올 수 있는 기능.
    *   `settings.json`에 `chart_templates` 항목 추가.
2.  **크로스헤어 동기화 (Crosshair Sync)**
    *   메인 차트와 서브 차트(RSI, MACD 등) 간의 X축(시간) 크로스헤어를 동기화.
    *   특정 시점에 마우스를 올리면 모든 보조지표의 해당 시점 값을 동시에 표시.
3.  **Y축 스케일링 (Dynamic Y-Axis)**
    *   서브 차트 추가 시 메인 차트의 높이가 너무 줄어들지 않도록, `Splitter`를 사용하여 사용자가 영역 크기를 조절할 수 있게 하거나 적절한 최소 높이 지정.

---

## 5. 작업 순서 (Implementation Plan)

1.  **관심종목 (Watchlist)**
    *   [ ] `ConfigLoader` 및 `settings.json` 구조 업데이트
    *   [ ] `WatchlistWidget` UI 구현 (그룹 관리, 검색, 테이블, **Drag&Drop**)
    *   [ ] `DataCollector` 연동 (그룹 변경 시 실시간 구독 갱신 로직, **100개 제한 처리**)
    *   [ ] `MainWindow`에 위젯 배치 및 테스트

2.  **차트 보조지표 (Chart Indicators)**
    *   [ ] `IndicatorEngine`: 필요한 지표 계산 함수 확인 및 보강
    *   [ ] `ChartWidget`: `GraphicsLayoutWidget` 구조로 리팩토링 (서브차트 지원, **Crosshair Sync**)
    *   [ ] `ChartSettingsDialog`: 지표 선택 및 파라미터 설정 UI 구현 (**템플릿 저장 기능 포함**)
    *   [ ] 차트 렌더링 로직 업데이트 (설정에 따라 동적 그리기)
