import sys
import os
from PyQt5.QtWidgets import QApplication

# Mock config if needed
sys.path.append(os.getcwd())

def verify():
    print("Verifying Backtester...")
    from ai.backtester import Backtester
    bt = Backtester()
    if hasattr(bt, 'reload_models'):
        print("[OK] Backtester.reload_models exists")
    else:
        print("[FAIL] Backtester.reload_models MISSING")
        return

    print("\nVerifying MainWindow UI...")
    app = QApplication(sys.argv)
    
    # Mock TradingManager to avoid async loop issues during test
    from unittest.mock import MagicMock
    import ui.main_window
    ui.main_window.TradingManager = MagicMock()
    
    from ui.main_window import MainWindow
    window = MainWindow()
    
    # Check Tabs
    tab_count = window.tabs.count()
    print(f"Tab Count: {tab_count}")
    
    expected_tabs = ["대시보드", "실시간 차트", "🤖 AI 트레이딩 & 백테스트", "관심종목", "💡 AI 추천"]
    # Note: Emojis in tab names might still be an issue for print, but let's try printing repr()
    
    found_tabs = []
    for i in range(tab_count):
        found_tabs.append(window.tabs.tabText(i))
        
    print(f"Found Tabs: {found_tabs}")
    
    all_found = True
    for tab in expected_tabs:
        if tab not in found_tabs:
            print(f"[FAIL] Missing Tab: {tab}")
            all_found = False
            
    if all_found:
        print("[OK] All expected tabs found")
        
    # Check Methods
    if hasattr(window, 'init_ai_tab'):
        print("[OK] init_ai_tab exists")
    else:
        print("[FAIL] init_ai_tab MISSING")
        
    if hasattr(window, 'run_backtest'):
        print("[OK] run_backtest exists")
    else:
        print("[FAIL] run_backtest MISSING")

if __name__ == "__main__":
    try:
        verify()
    except Exception as e:
        print(f"[FAIL] Verification Failed: {e}")
        import traceback
        traceback.print_exc()
