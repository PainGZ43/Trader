from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QStyledItemDelegate
from PyQt6.QtCore import Qt, pyqtSignal, QRectF
from PyQt6.QtGui import QColor, QBrush, QPainter, QPen

class OrderBookDelegate(QStyledItemDelegate):
    """
    Custom Delegate to draw volume bars behind the text.
    Expects Qt.ItemDataRole.UserRole to contain the volume ratio (0.0 to 1.0).
    """
    def __init__(self, parent=None, is_ask=True):
        super().__init__(parent)
        self.is_ask = is_ask
        # Colors matching the theme
        self.ask_color = QColor(84, 160, 255, 40)  # Blue with low opacity
        self.bid_color = QColor(255, 107, 107, 40) # Red with low opacity
        self.ask_bar_color = QColor(84, 160, 255, 80)
        self.bid_bar_color = QColor(255, 107, 107, 80)

    def paint(self, painter: QPainter, option, index):
        # Draw default background (selection etc)
        # self.initStyleOption(option, index) # Optional if we want default behavior
        
        # Get Volume Ratio
        ratio = index.data(Qt.ItemDataRole.UserRole)
        
        if ratio is not None and isinstance(ratio, float):
            painter.save()
            
            # Determine Bar Rect
            rect = option.rect
            width = rect.width() * ratio
            
            bar_rect = QRectF(rect.x(), rect.y(), width, rect.height())
            
            # Choose Color
            color = self.ask_bar_color if self.is_ask else self.bid_bar_color
            
            # Draw Bar
            painter.fillRect(bar_rect, color)
            
            painter.restore()
            
        # Draw Text
        super().paint(painter, option, index)


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
        
        # Set Delegates
        self.ask_delegate = OrderBookDelegate(self.table, is_ask=True)
        self.bid_delegate = OrderBookDelegate(self.table, is_ask=False)
        
        # Apply delegates to Volume columns (0 for Ask, 2 for Bid)
        # Actually, in our layout: Col 0 is Ask Vol, Col 1 is Price, Col 2 is Bid Vol?
        # Let's check update_orderbook logic.
        # _set_row: 
        #   if is_ask: setItem(row, 0, vol), setItem(row, 2, "")
        #   else: setItem(row, 0, ""), setItem(row, 2, vol)
        # So Col 0 is Ask Vol, Col 2 is Bid Vol.
        
        self.table.setItemDelegateForColumn(0, self.ask_delegate)
        self.table.setItemDelegateForColumn(2, self.bid_delegate)

        # Style (Basic overrides, main style in QSS)
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #2d2d2d;
                border: none;
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
        
        # Calculate Max Volume for Ratio
        max_vol = 1
        all_vols = [v for p, v in asks] + [v for p, v in bids]
        if all_vols:
            max_vol = max(all_vols)
        
        # Asks (Sell) - Display from high to low
        # We want the lowest ask at row 9, highest ask at row 0
        sorted_asks = sorted(asks, key=lambda x: x[0], reverse=True)
        if len(sorted_asks) > 10:
            sorted_asks = sorted_asks[-10:]
            
        # Fill Asks (Rows 0-9)
        for i in range(10):
            row_idx = 9 - i 
            if i < len(asks):
                price, vol = asks[i] # asks[0] is lowest ask
                ratio = vol / max_vol if max_vol > 0 else 0
                self._set_row(row_idx, price, vol, is_ask=True, ratio=ratio)
            else:
                self._clear_row(row_idx)

        # Fill Bids (Rows 10-19)
        for i in range(10):
            row_idx = 10 + i
            if i < len(bids):
                price, vol = bids[i]
                ratio = vol / max_vol if max_vol > 0 else 0
                self._set_row(row_idx, price, vol, is_ask=False, ratio=ratio)
            else:
                self._clear_row(row_idx)

    def _set_row(self, row, price, vol, is_ask, ratio=0.0):
        # Vol (Ask side)
        if is_ask:
            item = QTableWidgetItem(f"{vol:,}")
            item.setData(Qt.ItemDataRole.UserRole, ratio)
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 0, item)
            self.table.setItem(row, 2, QTableWidgetItem(""))
            color = QColor("#54a0ff") # Blueish for Asks
        else:
            self.table.setItem(row, 0, QTableWidgetItem(""))
            item = QTableWidgetItem(f"{vol:,}")
            item.setData(Qt.ItemDataRole.UserRole, ratio)
            item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 2, item)
            color = QColor("#ff6b6b") # Reddish for Bids
            
        # Price
        price_item = QTableWidgetItem(f"{price:,}")
        price_item.setForeground(color)
        price_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 1, price_item)
        
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
