import sys
import time
import threading
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
from core.event_bus import event_bus

def verify_integration():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    print("Starting Integration Verification...")
    
    async def run_tests():
        # Wait for loop to settle
        await asyncio.sleep(0.1)
        
        # 1. Test Backend -> UI (Macro Update)
        print("[TEST] Publishing 'market.data.macro'...")
        event_bus.publish("market.data.macro", {
            "indices": {"KOSPI": "2600.50", "KOSDAQ": "870.20"},
            "exchange_rate": "1310.5"
        })
        
        # 2. Test Backend -> UI (Account Update)
        print("[TEST] Publishing 'account.summary'...")
        event_bus.publish("account.summary", {
            "total_asset": 10000000,
            "deposit": 5000000,
            "total_pnl": 250000,
            "pnl_pct": 2.5
        })
        
        # 3. Test UI -> Backend (Order)
        def on_order_create(event):
            print(f"[SUCCESS] Backend received order: {event.data}")

        event_bus.subscribe("order.create", on_order_create)
        
        print("[TEST] Simulating 'BUY' click in OrderPanel...")
        window.order_panel.code_input.setText("005930")
        window.order_panel.qty_input.setValue(10)
        window.order_panel.price_input.setValue(70000)
        window.order_panel.btn_buy.click()
        
        # 4. Test Panic
        def on_panic(event):
            print(f"[SUCCESS] Backend received panic: {event.data}")
            
        event_bus.subscribe("system.panic", on_panic)
        print("[TEST] Simulating 'STOP ALGO' click...")
        window.order_panel.panic_signal.emit("STOP") 
        
        await asyncio.sleep(2)
        app.quit()

    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    with loop:
        loop.create_task(run_tests())
        loop.run_forever()
    
    print("Verification Finished.")

import asyncio
import qasync

if __name__ == "__main__":
    verify_integration()
