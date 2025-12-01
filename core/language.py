import json
import os
from core.config import config
from core.logger import get_logger

class LanguageManager:
    _instance = None
    
    TRANSLATIONS = {
        "ko": {
            # MainWindow
            "window_title": "PainTrader AI - Pro",
            "dock_strategy": "전략 및 계좌",
            "dock_execution": "주문 및 체결",
            "dock_logs": "로그 및 기록",
            
            # HeaderBar
            "header_title": "PainTrader AI",
            "btn_start": " 시작",
            "btn_stop": " 정지",
            "cpu": "CPU",
            "mem": "메모리",
            "lat": "지연",
            
            # Dashboard
            "kospi": "코스피",
            "kosdaq": "코스닥",
            "usd_krw": "원/달러",
            
            # ControlPanel
            "total_asset": "총 자산",
            "deposit": "예수금",
            "pnl": "손익",
            "col_symbol": "종목코드",
            "col_name": "종목명",
            "col_avg": "평단가",
            "col_cur": "현재가",
            "col_pnl": "수익률",
            "col_action": "주문",
            
            # OrderPanel
            "lbl_code": "종목코드:",
            "lbl_price": "가격:",
            "lbl_qty": "수량:",
            "btn_mkt": "시장가",
            "btn_buy": "매수",
            "btn_sell": "매도",
            "panic_title": "⚠️ 긴급 제어",
            "btn_stop_algo": "알고리즘 정지",
            "btn_cancel_all": "전체 취소",
            "btn_liquidate": "전량 청산",
            "msg_liquidate_title": "청산 확인",
            "msg_liquidate_body": "정말 모든 포지션을 시장가로 청산하시겠습니까?\n이 작업은 되돌릴 수 없습니다.",
            
            # LogViewer
            "log_search": "검색...",
            "chk_autoscroll": "자동 스크롤",
            "btn_save": "저장",
            
            # Settings
            "settings_title": "설정",
            "tab_account": "계좌 & API",
            "tab_strategy": "전략 튜닝",
            "tab_risk": "리스크 & 알림",
            "tab_system": "시스템 상태",
            "lbl_language": "언어 (Language):",
            "lbl_loglevel": "로그 레벨:",
            "lbl_sim_mode": "모드:",
            "chk_sim_mode": "모의투자 모드 (Simulation)",
            "btn_save_settings": "저장",
            "btn_cancel_settings": "취소",
            "msg_restart_title": "재시작 필요",
            "msg_restart_body": "언어 설정을 적용하려면 프로그램을 재시작해야 합니다.",
            
            # Common
            "error": "오류",
            "warning": "경고",
            "info": "알림"
        },
        "en": {
            # MainWindow
            "window_title": "PainTrader AI - Pro",
            "dock_strategy": "Strategy & Account",
            "dock_execution": "Execution",
            "dock_logs": "Logs & History",
            
            # HeaderBar
            "header_title": "PainTrader AI",
            "btn_start": " Start",
            "btn_stop": " Stop",
            "cpu": "CPU",
            "mem": "MEM",
            "lat": "LAT",
            
            # Dashboard
            "kospi": "KOSPI",
            "kosdaq": "KOSDAQ",
            "usd_krw": "USD/KRW",
            
            # ControlPanel
            "total_asset": "Total Asset",
            "deposit": "Cash",
            "pnl": "P&L",
            "col_symbol": "Symbol",
            "col_name": "Name",
            "col_avg": "Avg Price",
            "col_cur": "Cur Price",
            "col_pnl": "P&L %",
            "col_action": "Action",
            
            # OrderPanel
            "lbl_code": "Code:",
            "lbl_price": "Price:",
            "lbl_qty": "Qty:",
            "btn_mkt": "MKT",
            "btn_buy": "BUY",
            "btn_sell": "SELL",
            "panic_title": "⚠️ EMERGENCY",
            "btn_stop_algo": "STOP ALGO",
            "btn_cancel_all": "CANCEL ALL",
            "btn_liquidate": "LIQUIDATE ALL",
            "msg_liquidate_title": "Confirm Liquidation",
            "msg_liquidate_body": "Are you sure you want to LIQUIDATE ALL positions?\nThis action cannot be undone.",
            
            # LogViewer
            "log_search": "Search...",
            "chk_autoscroll": "Auto Scroll",
            "btn_save": "Save",
            
            # Settings
            "settings_title": "Settings",
            "tab_account": "Accounts & API",
            "tab_strategy": "Strategy Tuning",
            "tab_risk": "Risk & Notification",
            "tab_system": "System Health",
            "lbl_language": "Language:",
            "lbl_loglevel": "Log Level:",
            "lbl_sim_mode": "Mode:",
            "chk_sim_mode": "Enable Paper Trading (Simulation)",
            "btn_save_settings": "Save",
            "btn_cancel_settings": "Cancel",
            "msg_restart_title": "Restart Required",
            "msg_restart_body": "You must restart the application to apply language changes.",
            
            # Common
            "error": "Error",
            "warning": "Warning",
            "info": "Info"
        }
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LanguageManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.logger = get_logger("LanguageManager")
        # Load language from config, default to 'ko'
        self.current_lang = config.get("system.language", "ko")
        self.logger.info(f"Language initialized: {self.current_lang}")

    def set_language(self, lang_code: str):
        if lang_code in self.TRANSLATIONS:
            self.current_lang = lang_code
            config.set("system.language", lang_code)
            self.logger.info(f"Language changed to: {lang_code}")
            return True
        return False

    def get_text(self, key: str) -> str:
        """Get translated text for the key."""
        lang_dict = self.TRANSLATIONS.get(self.current_lang, self.TRANSLATIONS["ko"])
        return lang_dict.get(key, key)

language_manager = LanguageManager()
