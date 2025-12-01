from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QSpinBox, QFrame, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal
from core.language import language_manager

class OrderPanel(QWidget):
    send_order_signal = pyqtSignal(dict) # {type, code, price, qty}
    panic_signal = pyqtSignal(str) # "STOP", "CANCEL_ALL", "LIQUIDATE"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        # 1. Order Form
        form_group = QFrame()
        form_group.setStyleSheet("background-color: #252526; border-radius: 4px; padding: 5px;")
        form_layout = QVBoxLayout(form_group)
        
        # Symbol Input
        row1 = QHBoxLayout()
        row1.addWidget(QLabel(language_manager.get_text("lbl_code")))
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("005930")
        row1.addWidget(self.code_input)
        form_layout.addLayout(row1)
        
        # Price Input
        row2 = QHBoxLayout()
        row2.addWidget(QLabel(language_manager.get_text("lbl_price")))
        self.price_input = QSpinBox()
        self.price_input.setRange(0, 10000000)
        self.price_input.setSingleStep(100)
        row2.addWidget(self.price_input)
        
        self.market_chk = QPushButton(language_manager.get_text("btn_mkt"))
        self.market_chk.setCheckable(True)
        self.market_chk.setFixedWidth(40)
        self.market_chk.setStyleSheet("""
            QPushButton:checked { background-color: #3498db; color: white; }
            QPushButton { background-color: #3c3c3c; color: #ccc; }
        """)
        self.market_chk.toggled.connect(self.on_market_toggled)
        row2.addWidget(self.market_chk)
        form_layout.addLayout(row2)
        
        # Quantity Input
        row3 = QHBoxLayout()
        row3.addWidget(QLabel(language_manager.get_text("lbl_qty")))
        self.qty_input = QSpinBox()
        self.qty_input.setRange(1, 100000)
        row3.addWidget(self.qty_input)
        form_layout.addLayout(row3)
        
        # Quick Qty Buttons
        qty_btn_layout = QHBoxLayout()
        for pct in ["10%", "25%", "50%", "100%"]:
            btn = QPushButton(pct)
            btn.setFixedHeight(20)
            btn.setStyleSheet("font-size: 10px; padding: 2px;")
            btn.clicked.connect(lambda checked, p=pct: self.on_quick_qty(p))
            qty_btn_layout.addWidget(btn)
        form_layout.addLayout(qty_btn_layout)
        
        # Buy/Sell Buttons
        action_layout = QHBoxLayout()
        self.btn_buy = QPushButton(language_manager.get_text("btn_buy"))
        self.btn_buy.setStyleSheet("background-color: #ff6b6b; color: white; font-weight: bold; padding: 8px;")
        self.btn_buy.clicked.connect(lambda: self.on_send_order("BUY"))
        
        self.btn_sell = QPushButton(language_manager.get_text("btn_sell"))
        self.btn_sell.setStyleSheet("background-color: #54a0ff; color: white; font-weight: bold; padding: 8px;")
        self.btn_sell.clicked.connect(lambda: self.on_send_order("SELL"))
        
        action_layout.addWidget(self.btn_buy)
        action_layout.addWidget(self.btn_sell)
        form_layout.addLayout(action_layout)
        
        layout.addWidget(form_group)
        
        layout.addStretch()
        
        # 2. Panic Button Section
        panic_group = QFrame()
        panic_group.setStyleSheet("border: 1px solid #d32f2f; border-radius: 4px; padding: 5px;")
        panic_layout = QVBoxLayout(panic_group)
        
        lbl = QLabel(language_manager.get_text("panic_title"))
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color: #d32f2f; font-weight: bold;")
        panic_layout.addWidget(lbl)
        
        # Stop Algo
        btn_stop = QPushButton(language_manager.get_text("btn_stop_algo"))
        btn_stop.clicked.connect(lambda: self.panic_signal.emit("STOP"))
        panic_layout.addWidget(btn_stop)
        
        # Cancel All
        btn_cancel = QPushButton(language_manager.get_text("btn_cancel_all"))
        btn_cancel.clicked.connect(lambda: self.panic_signal.emit("CANCEL_ALL"))
        panic_layout.addWidget(btn_cancel)
        
        # Liquidate (Double Click Required)
        self.btn_liquidate = QPushButton(language_manager.get_text("btn_liquidate"))
        self.btn_liquidate.setObjectName("PanicButton") # Uses red style from qss
        self.btn_liquidate.setStyleSheet("background-color: #b71c1c; color: white; font-weight: bold; padding: 5px;")
        # Custom logic for double click could be added, for now we use confirmation dialog
        self.btn_liquidate.clicked.connect(self.on_liquidate_click)
        panic_layout.addWidget(self.btn_liquidate)
        
        layout.addWidget(panic_group)

    def on_market_toggled(self, checked):
        self.price_input.setDisabled(checked)
        if checked:
            self.price_input.setValue(0)

    def on_quick_qty(self, pct_str):
        # Placeholder logic. Needs account info to calculate real qty.
        print(f"Quick Qty: {pct_str}")

    def on_send_order(self, side):
        code = self.code_input.text()
        if not code:
            return
            
        order = {
            "type": side,
            "code": code,
            "price": 0 if self.market_chk.isChecked() else self.price_input.value(),
            "qty": self.qty_input.value()
        }
        self.send_order_signal.emit(order)

    def on_liquidate_click(self):
        # Confirmation Dialog
        reply = QMessageBox.question(
            self, language_manager.get_text("msg_liquidate_title"), 
            language_manager.get_text("msg_liquidate_body"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.panic_signal.emit("LIQUIDATE")
