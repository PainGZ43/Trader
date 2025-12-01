from core.config import config
from ui.widgets.settings_tabs import StrategySettingsTab, RiskSettingsTab, SystemSettingsTab
from PyQt6.QtWidgets import QApplication
import sys

def verify_settings_persistence():
    app = QApplication(sys.argv)
    
    print("Verifying Settings Persistence...")
    
    # 1. Test Risk Settings
    print("[TEST] Risk Settings...")
    risk_tab = RiskSettingsTab()
    risk_tab.max_loss.setValue(5)
    risk_tab.max_pos.setValue(20)
    risk_tab.kakao_token.setText("TEST_SECURE_TOKEN")
    risk_tab.save_settings()
    
    from core.secure_storage import secure_storage
    stored_token = secure_storage.get("kakao_token")
    
    if config.get("risk.max_loss_pct") == 5 and \
       config.get("risk.max_position_pct") == 20 and \
       stored_token == "TEST_SECURE_TOKEN":
        print("[PASS] Risk settings saved (Token in SecureStorage).")
    else:
        print(f"[FAIL] Risk settings mismatch. Token: {stored_token}")

    # 2. Test System Settings
    print("[TEST] System Settings...")
    sys_tab = SystemSettingsTab()
    sys_tab.log_level.setCurrentText("DEBUG")
    sys_tab.sim_mode.setChecked(False)
    sys_tab.save_settings()
    
    if config.get("system.log_level") == "DEBUG" and \
       config.get("system.simulation_mode") == False:
        print("[PASS] System settings saved.")
    else:
        print(f"[FAIL] System settings mismatch: {config.get('system.log_level')}, {config.get('system.simulation_mode')}")

    # 3. Test Strategy Settings
    print("[TEST] Strategy Settings...")
    strat_tab = StrategySettingsTab()
    # Select first item
    strat_tab.strategy_list.setCurrentItem(strat_tab.strategy_list.item(0, 0))
    strat_tab.load_parameters(strat_tab.strategy_list.item(0, 0))
    
    # Modify a value (assuming HybridStrategy has rsi_period)
    if "rsi_period" in strat_tab.param_widgets:
        strat_tab.param_widgets["rsi_period"].setValue(20)
        strat_tab.save_settings()
        
        if config.get("strategy.HybridStrategy.rsi_period") == 20:
            print("[PASS] Strategy settings saved.")
        else:
            print(f"[FAIL] Strategy settings mismatch: {config.get('strategy.HybridStrategy.rsi_period')}")
    else:
        print("[SKIP] rsi_period widget not found.")

    print("Verification Complete.")

if __name__ == "__main__":
    verify_settings_persistence()
