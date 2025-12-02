import sys
import os
import pandas as pd
import numpy as np

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data.indicator_engine import indicator_engine
from PyQt6.QtWidgets import QApplication
from ui.widgets.chart_settings_dialog import ChartSettingsDialog

def verify_indicator_engine():
    print("Verifying Indicator Engine...")
    
    # Create Mock Data
    data = {
        'open': np.random.rand(100) * 100,
        'high': np.random.rand(100) * 100,
        'low': np.random.rand(100) * 100,
        'close': np.random.rand(100) * 100,
        'volume': np.random.rand(100) * 1000
    }
    df = pd.DataFrame(data)
    
    # Test MACD
    macd = indicator_engine.get_indicator(df, "MACD", fastperiod=12, slowperiod=26, signalperiod=9)
    assert isinstance(macd, dict)
    assert "macd" in macd
    print("[OK] MACD Calculation")
    
    # Test BBANDS
    bb = indicator_engine.get_indicator(df, "BBANDS", timeperiod=20)
    assert isinstance(bb, dict)
    assert "upper" in bb
    print("[OK] BBANDS Calculation")
    
    # Test STOCH
    stoch = indicator_engine.get_indicator(df, "STOCH")
    assert isinstance(stoch, dict)
    assert "k" in stoch
    print("[OK] STOCH Calculation")

def verify_settings_dialog():
    print("Verifying Chart Settings Dialog...")
    app = QApplication(sys.argv)
    
    dialog = ChartSettingsDialog()
    
    # Test Adding Indicator
    # Mock selection
    dialog.list_available.setCurrentRow(0) # SMA
    dialog.add_indicator()
    
    indicators = dialog.get_indicators()
    assert len(indicators) == 1
    assert indicators[0]["name"] == "SMA"
    print("[OK] Add Indicator")
    
    # Test Removing
    dialog.list_active.setCurrentRow(0)
    dialog.remove_indicator()
    assert len(dialog.get_indicators()) == 0
    print("[OK] Remove Indicator")
    
    # app.exec() # Don't run loop

if __name__ == "__main__":
    verify_indicator_engine()
    verify_settings_dialog()
