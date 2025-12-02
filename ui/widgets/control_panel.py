from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QFrame
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from core.language import language_manager

class ControlPanel(QWidget):
    close_position_signal = pyqtSignal(str) # Symbol to close

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        # 1. Account Summary Section
        summary_group = QFrame()
        summary_group.setStyleSheet("background-color: #252526; border-radius: 4px; padding: 5px;")
        summary_layout = QVBoxLayout(summary_group)
        
        # Row 1: Total Asset
        row1 = QHBoxLayout()
        self.total_asset_label = QLabel(f"{language_manager.get_text('total_asset')}: 0 KRW")
        self.total_asset_label.setStyleSheet("font-size: 14px; font-weight: bold; color: white;")
        row1.addWidget(self.total_asset_label)
        summary_layout.addLayout(row1)
        
        # Row 2: Deposit & P&L
        row2 = QHBoxLayout()
        self.deposit_label = QLabel(f"{language_manager.get_text('deposit')}: 0 KRW")
        self.deposit_label.setStyleSheet("color: #cccccc;")
        
        self.pnl_label = QLabel(f"{language_manager.get_text('pnl')}: 0 (0.00%)")
        self.pnl_label.setStyleSheet("color: #cccccc;")
        
        row2.addWidget(self.deposit_label)
        row2.addWidget(self.pnl_label)
        summary_layout.addLayout(row2)
        
        layout.addWidget(summary_group)

        # 2. Portfolio Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            language_manager.get_text("col_symbol"),
            language_manager.get_text("col_name"),
            language_manager.get_text("col_avg"),
            language_manager.get_text("col_cur"),
            language_manager.get_text("col_pnl"),
            language_manager.get_text("col_action")
        ])
        
        # Style
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
                padding: 4px;
                border: 1px solid #333;
            }
        """)
        
        layout.addWidget(self.table)
        
        # Initialize with empty portfolio
        self.update_portfolio([])

    def update_account_summary(self, total_asset, deposit, total_pnl, pnl_pct):
        self.total_asset_label.setText(f"{language_manager.get_text('total_asset')}: {total_asset:,.0f} KRW")
        self.deposit_label.setText(f"{language_manager.get_text('deposit')}: {deposit:,.0f} KRW")
        
        pnl_text = f"{language_manager.get_text('pnl')}: {total_pnl:,.0f} ({pnl_pct:+.2f}%)"
        self.pnl_label.setText(pnl_text)
        
        if total_pnl > 0:
            self.pnl_label.setStyleSheet("color: #ff6b6b; font-weight: bold;")
        elif total_pnl < 0:
            self.pnl_label.setStyleSheet("color: #54a0ff; font-weight: bold;")
        else:
            self.pnl_label.setStyleSheet("color: #cccccc;")

    def update_portfolio(self, holdings: list):
        """
        holdings: list of dicts
        """
        self.table.setRowCount(0)
        
        if not holdings:
            self.table.setRowCount(1)
            item = QTableWidgetItem(language_manager.get_text("msg_no_positions", "No positions"))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(0, 0, item)
            self.table.setSpan(0, 0, 1, 6)
            return

        self.table.setRowCount(len(holdings))
        
        for row, item in enumerate(holdings):
            code = item.get("code", "")
            name = item.get("name", "")
            avg = item.get("avg_price", 0)
            cur = item.get("current_price", 0)
            qty = item.get("qty", 0)
            
            # Calculate P&L
            if avg > 0:
                pnl_pct = (cur - avg) / avg * 100
                pnl_amt = (cur - avg) * qty
            else:
                pnl_pct = 0
                pnl_amt = 0
            
            self.table.setItem(row, 0, QTableWidgetItem(code))
            self.table.setItem(row, 1, QTableWidgetItem(name))
            self.table.setItem(row, 2, QTableWidgetItem(f"{avg:,.0f}"))
            self.table.setItem(row, 3, QTableWidgetItem(f"{cur:,.0f}"))
            
            pnl_item = QTableWidgetItem(f"{pnl_pct:+.2f}%")
            if pnl_pct > 0:
                pnl_item.setForeground(QColor("#ff6b6b"))
            elif pnl_pct < 0:
                pnl_item.setForeground(QColor("#54a0ff"))
            self.table.setItem(row, 4, pnl_item)
            
            # Close Button
            btn = QPushButton("X")
            btn.setFixedSize(20, 20)
            btn.setStyleSheet("background-color: #e74c3c; color: white; border: none; border-radius: 2px;")
            btn.clicked.connect(lambda checked, s=code: self.close_position_signal.emit(s))
            
            # Center the button
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(0,0,0,0)
            btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            btn_layout.addWidget(btn)
            
            self.table.setCellWidget(row, 5, btn_widget)
