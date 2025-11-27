    *   **트레이더 (Trader)**: 미체결 주문 감시, 정정/취소 주문, 잔고 편입 확인.
    *   **알림 (Notifier) - 카카오톡 중심**:
        *   **메인 채널**: **카카오톡 (KakaoTalk)**.
        *   **알림 유형**: 매매 체결, 에러, 일일 리포트, AI 신호, 조건검색 포착.
    *   **트레이더 (Trader)**: 미체결 주문 감시, 정정/취소 주문, 잔고 편입 확인.
    *   **알림 (Notifier) - 카카오톡 중심**:
        *   **메인 채널**: **카카오톡 (KakaoTalk)**.
        *   **알림 유형**: 매매 체결, 에러, 일일 리포트, AI 신호, 조건검색 포착.
    *   **트레이더 (Trader)**: 미체결 주문 감시, 정정/취소 주문, 잔고 편입 확인.
    *   **알림 (Notifier) - 카카오톡 중심**:
        *   **메인 채널**: **카카오톡 (KakaoTalk)**.
        *   **알림 유형**: 매매 체결, 에러, 일일 리포트, AI 신호, 조건검색 포착.
    *   **트레이더 (Trader)**: 미체결 주문 감시, 정정/취소 주문, 잔고 편입 확인.
    *   **알림 (Notifier) - 카카오톡 중심**:
        *   **메인 채널**: **카카오톡 (KakaoTalk)**.
        *   **알림 유형**: 매매 체결, 에러, 일일 리포트, AI 신호, 조건검색 포착.


### Dialogs
#### [NEW] [ui/settings_dialog.py](file:///e:/GitHub/Trader/PainTrader/ui/settings_dialog.py)
- **Tabs**: General, Account (API Keys), Strategy (Params), Risk (Limits), Notification.
- **Condition Search**: List of loaded conditions with checkboxes to enable/disable.
- **Optimization**: Grid search setup (Min/Max/Step) and results table with "Apply" button.
- **Security**: Uses `SecureStorage` for API keys.

#### [NEW] [ui/log_viewer.py](file:///e:/GitHub/Trader/PainTrader/ui/log_viewer.py)
- **`LogTable`**: Filterable table for system logs.
- **`SystemHealth`**: Dedicated tab/view for `SYSTEM_WARNING` events and resource usage history.
- **`TradeHistory`**: List of executed trades.

## Proposed Changes
*   **데이터베이스**: SQLite.

## 4. 워크플로우
1.  **초기화**: 자동 로그인, DB 연결, 키움 API 초기화.
2.  **데이터 루프**: 실시간 데이터(주식체결, 주식호가) + 조건검색 실시간 편입.
3.  **분석**: 지표 업데이트 -> AI 모델/전략 판단.
4.  **결정**: 매수/매도 신호 생성 -> 리스크 관리 확인.
5.  **실행**: 주문 전송 -> 체결 확인 -> DB 업데이트.
6.  **피드백**: 결과 로깅.

## 5. 다음 단계 (확정)
*   **타겟 시장**: **국내 주식 (Kiwoom) 단독**.
*   **AI 접근 방식**: 사용자 선택 가능.
*   **매매 전략**: 사용자 선택 가능.
*   **UI 프레임워크**: PyQt (데스크탑).
*   **상세 설계 시작**: 데이터 수집 및 처리 모듈 (키움 전용).

## 6. 추가 고려사항 (키움 특화)
*   **모의 투자**: 키움증권 상시 모의투자 시스템 활용.
*   **32비트 제약**: Python 32bit 환경 구성 필수. AI 라이브러리 호환성 문제 시 **64비트 AI 서버와 통신(Socket/ZMQ)**하는 구조 고려 필요.
*   **자동 로그인**: KOA Studio 등을 활용한 자동 로그인 설정.
