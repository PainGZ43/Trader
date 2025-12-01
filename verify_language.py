from core.language import language_manager
from core.config import config

def verify_language_switch():
    print("Verifying Language Switching...")
    
    # 1. Check Default (Korean)
    print(f"Current Lang: {language_manager.current_lang}")
    print(f"Text 'window_title' (KO): {language_manager.get_text('window_title')}")
    
    if language_manager.get_text("btn_start") == " 시작":
        print("[PASS] Default Korean text correct.")
    else:
        print(f"[FAIL] Default text mismatch: {language_manager.get_text('btn_start')}")

    # 2. Switch to English
    print("Switching to English...")
    language_manager.set_language("en")
    
    print(f"Current Lang: {language_manager.current_lang}")
    print(f"Text 'window_title' (EN): {language_manager.get_text('window_title')}")
    
    if language_manager.get_text("btn_start") == " Start":
        print("[PASS] English text correct.")
    else:
        print(f"[FAIL] English text mismatch: {language_manager.get_text('btn_start')}")

    # 3. Verify Persistence
    saved_lang = config.get("system.language")
    if saved_lang == "en":
        print("[PASS] Language setting saved to config.")
    else:
        print(f"[FAIL] Config not updated: {saved_lang}")

    # Reset to Korean for user
    language_manager.set_language("ko")
    print("Reset to Korean.")

if __name__ == "__main__":
    verify_language_switch()
