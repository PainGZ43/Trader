import sys
import os
import traceback

# Add project root to sys.path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

try:
    print(f"Testing import from {project_root}")
    from ui.settings_dialog import SettingsDialog
    print("SUCCESS: SettingsDialog import successful")
except Exception as e:
    print(f"FAILURE: SettingsDialog import failed: {e}")
    traceback.print_exc()
    sys.exit(1)
