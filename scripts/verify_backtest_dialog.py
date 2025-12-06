import sys
import os
sys.path.append(os.getcwd())

from PyQt6.QtWidgets import QApplication
from ui.backtest_dialog import BacktestDialog
from strategy.registry import StrategyRegistry

def verify():
    print("Starting verification...")
    app = QApplication(sys.argv)
    
    # Initialize Registry
    print("Initializing StrategyRegistry...")
    StrategyRegistry.initialize()
    
    try:
        # Instantiate Dialog
        print("Instantiating BacktestDialog...")
        dialog = BacktestDialog()
        print("BacktestDialog instantiated successfully.")
        
        # Check if Optimization UI is initialized (it's done in __init__)
        # We can try to switch strategy to trigger load_opt_params again just to be sure
        if hasattr(dialog, 'opt_strategy_combo'):
            current = dialog.opt_strategy_combo.currentText()
            print(f"Current Strategy in Opt Tab: {current}")
            # This was the point of failure (UnboundLocalError)
            dialog.load_opt_params(current)
            print("load_opt_params executed successfully.")
            
        print("Verification Passed!")
        return 0
    except Exception as e:
        print(f"Verification Failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(verify())
