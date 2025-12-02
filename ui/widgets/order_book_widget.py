from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QBrush, QLinearGradient

class OrderBookWidget(QWidget):
    order_clicked = pyqtSignal(float) # Signal price when clicked

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Vol", "Price", "Vol"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.cellDoubleClicked.connect(self.on_cell_double_clicked)
        
        # Style
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
                padding: 4px;
                border: 1px solid #333;
            }
        """)
        
        self.layout.addWidget(self.table)
        
        # Initialize with waiting message
        self.table.setRowCount(1)
        item = QTableWidgetItem("Waiting for data...")
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(0, 0, item)
        self.table.setSpan(0, 0, 1, 3)

    def update_orderbook(self, asks, bids):
        """
        asks: list of (price, volume) sorted by price ascending
        bids: list of (price, volume) sorted by price descending
        """
        # Clear table logic if needed, but here we just update cells
        if not asks and not bids:
            self.table.setRowCount(1)
            item = QTableWidgetItem("Waiting for data...")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(0, 0, item)
            self.table.setSpan(0, 0, 1, 3)
            return

        if self.table.rowCount() != 20:
             self.table.setRowCount(20)
             self.table.clearSpans()
        
        # Asks (Sell) - Display from high to low (so lowest ask is near center)
        # We want the lowest ask at row 9, highest ask at row 0
        # asks usually come sorted by price ascending (lowest first)
        # So we take first 10 asks, reverse them to put high price at top
        
        display_asks = sorted(asks, key=lambda x: x[0], reverse=True)[-10:] 
        # Actually standard order book view:
        # Top: High Ask
        # ...
        # Center: Low Ask
        # Center: High Bid
        # ...
        # Bottom: Low Bid
        
        # So we need asks sorted descending.
        # If input asks is [100, 101, 102], we want to display 102, 101, 100.
        
        sorted_asks = sorted(asks, key=lambda x: x[0], reverse=True)
        # Take last 10 if more than 10, or pad
        if len(sorted_asks) > 10:
            sorted_asks = sorted_asks[-10:]
            
        # Fill Asks (Rows 0-9)
        for i in range(10):
            row_idx = 9 - i # Fill from bottom of ask section (9) up to 0
            if i < len(asks):
                price, vol = asks[i] # asks[0] is lowest ask
                self._set_row(row_idx, price, vol, is_ask=True)
            else:
                self._clear_row(row_idx)

        # Fill Bids (Rows 10-19)
        # Bids sorted descending (highest first). bids[0] is highest bid.
        for i in range(10):
            row_idx = 10 + i
            if i < len(bids):
                price, vol = bids[i]
                self._set_row(row_idx, price, vol, is_ask=False)
            else:
                self._clear_row(row_idx)

    def _set_row(self, row, price, vol, is_ask):
        # Vol (Ask side)
        if is_ask:
            self.table.setItem(row, 0, QTableWidgetItem(str(vol)))
            self.table.setItem(row, 2, QTableWidgetItem(""))
            color = QColor("#54a0ff") # Blueish for Asks
        else:
            self.table.setItem(row, 0, QTableWidgetItem(""))
            self.table.setItem(row, 2, QTableWidgetItem(str(vol)))
            color = QColor("#ff6b6b") # Reddish for Bids
            
        # Price
        price_item = QTableWidgetItem(str(price))
        price_item.setForeground(color)
        price_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 1, price_item)
        
        # Background bar for volume (Simplified)
        # In a real app, we would use a custom delegate to draw a bar
        
    def _clear_row(self, row):
        for col in range(3):
            self.table.setItem(row, col, QTableWidgetItem(""))

    def on_cell_double_clicked(self, row, col):
        item = self.table.item(row, 1) # Price column
        if item and item.text():
            try:
                price = float(item.text().replace(",", ""))
                self.order_clicked.emit(price)
            except ValueError:
                pass
