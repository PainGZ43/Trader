import sys
import asyncio
import os
from PyQt6.QtWidgets import QApplication
from qasync import QEventLoop

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ui.main_window import MainWindow
from core.event_bus import event_bus
from data.kiwoom_rest_client import kiwoom_client
from execution.engine import ExecutionEngine
from core.config import config

async def verify_startup():
    print("=== Verifying Full Startup & Account Loading ===")
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    # Initialize Engine
    print("Initializing Execution Engine...")
    exec_engine = ExecutionEngine(kiwoom_client, mode="REAL", config=config._config)
    await exec_engine.initialize()
    
    # Wait for Account Summary Event
    print("Waiting for Account Summary...")
    
    future = asyncio.get_event_loop().create_future()
    
    def on_summary(event):
        print("[SUCCESS] Account Summary Received!")
        print(event.data)
        if not future.done():
            future.set_result(True)
            
    event_bus.subscribe("account.summary", on_summary)
    
    try:
        await asyncio.wait_for(future, timeout=10.0)
    except asyncio.TimeoutError:
        print("[FAIL] Timeout waiting for Account Summary.")
    
    # Cleanup
    await kiwoom_client.close()
    # app.quit() # Can't quit easily in script without blocking
    print("=== Verification Complete ===")

if __name__ == "__main__":
    loop = QEventLoop(QApplication.instance() or QApplication(sys.argv))
    asyncio.set_event_loop(loop)
    with loop:
        loop.run_until_complete(verify_startup())
