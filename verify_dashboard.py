import sys
import os
from PyQt6.QtWidgets import QApplication
from ui.dashboard import Dashboard
from ui.widgets.chart_widget import ChartWidget
from ui.widgets.order_book_widget import OrderBookWidget

def verify_dashboard():
    app = QApplication(sys.argv)
    
    print("Initializing Dashboard...")
    try:
        dashboard = Dashboard()
        dashboard.show()
        print("Dashboard initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize Dashboard: {e}")
        return

    print("Checking child widgets...")
    chart = dashboard.findChild(ChartWidget)
    orderbook = dashboard.findChild(OrderBookWidget)
    
    if chart:
        print("ChartWidget found.")
    else:
        print("ERROR: ChartWidget not found.")
        
    if orderbook:
        print("OrderBookWidget found.")
    else:
        print("ERROR: OrderBookWidget not found.")
        
    print("Verification complete. Closing in 3 seconds...")
    # QTimer.singleShot(3000, app.quit)
    # app.exec() # Uncomment to see UI

if __name__ == "__main__":
    verify_dashboard()
