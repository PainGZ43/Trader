from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

class Dashboard(QWidget):
    # Signal for thread-safe UI update
    data_received = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.init_ui()
        
        # Connect signal
        self.data_received.connect(self.process_data)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 1. Macro Data Section (Top)
        macro_layout = QHBoxLayout()
        self.kospi_label = QLabel("KOSPI: -")
        self.kosdaq_label = QLabel("KOSDAQ: -")
        self.usd_label = QLabel("USD/KRW: -")
        
        # Style labels
        for label in [self.kospi_label, self.kosdaq_label, self.usd_label]:
            label.setStyleSheet("color: #cccccc; font-size: 14px; font-weight: bold; padding: 5px; background: #2d2d2d; border-radius: 4px;")
            macro_layout.addWidget(label)
            
        macro_layout.addStretch()
        layout.addLayout(macro_layout)

        # 2. Real-time Market Data Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Symbol", "Name", "Price", "Change", "Volume"])
        
        # Table Style
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                color: white;
                gridline-color: #333;
                border: none;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: white;
                padding: 5px;
                border: 1px solid #333;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
            }
        """)
        
        layout.addWidget(self.table)

        # Add Dummy Data for Visualization
        self.add_dummy_data()

    def add_dummy_data(self):
        data = [
            ("005930", "Samsung Elec", "70,500", "+1.2%", "10,500,000"),
            ("000660", "SK Hynix", "120,000", "-0.5%", "3,200,000"),
            ("035420", "NAVER", "210,000", "+0.0%", "500,000"),
        ]
        
        self.table.setRowCount(len(data))
        for row, (code, name, price, change, vol) in enumerate(data):
            self.table.setItem(row, 0, QTableWidgetItem(code))
            self.table.setItem(row, 1, QTableWidgetItem(name))
            self.table.setItem(row, 2, QTableWidgetItem(price))
            
            change_item = QTableWidgetItem(change)
            if "+" in change:
                change_item.setForeground(QColor("#ff6b6b")) # Red for up
            elif "-" in change:
                change_item.setForeground(QColor("#54a0ff")) # Blue for down
            self.table.setItem(row, 3, change_item)
            
            self.table.setItem(row, 4, QTableWidgetItem(vol))

    def on_data_received(self, data):
        """
        Callback called by DataCollector (background thread).
        Emits signal to update UI on main thread.
        """
        self.data_received.emit(data)

    def process_data(self, data):
        """
        Slot to update UI.
        """
        event_type = data.get("type")
        
        if event_type == "MACRO":
            indices = data.get("indices", {})
            rate = data.get("exchange_rate", 0.0)
            self.kospi_label.setText(f"KOSPI: {indices.get('KOSPI', '-')}")
            self.kosdaq_label.setText(f"KOSDAQ: {indices.get('KOSDAQ', '-')}")
            self.usd_label.setText(f"USD/KRW: {rate}")
            
        elif event_type == "REALTIME":
            symbol = data.get("code")
            price = data.get("price")
            change = data.get("change", "0.0%") 
            volume = data.get("volume", 0)
            
            if symbol:
                self.update_market_data(symbol, str(price), str(change), str(volume))

    def update_market_data(self, symbol, price, change, volume):
        # Find row for symbol
        row = -1
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item and item.text() == symbol:
                row = r
                break
        
        # If not found, add new row
        if row == -1:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(symbol))
            self.table.setItem(row, 1, QTableWidgetItem(symbol)) # Name placeholder
        
        # Update columns
        self.table.setItem(row, 2, QTableWidgetItem(str(price)))
        
        change_item = QTableWidgetItem(str(change))
        if "+" in str(change):
            change_item.setForeground(QColor("#ff6b6b"))
        elif "-" in str(change):
            change_item.setForeground(QColor("#54a0ff"))
        self.table.setItem(row, 3, change_item)
        
        self.table.setItem(row, 4, QTableWidgetItem(str(volume)))
