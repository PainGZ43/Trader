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

        # 1. Account Summary Section (Grid 2x3)
        summary_group = QFrame()
        summary_group.setStyleSheet("background-color: #252526; border-radius: 4px; padding: 5px;")
        summary_layout = QVBoxLayout(summary_group)
        
        from PyQt6.QtWidgets import QGridLayout
        grid = QGridLayout()
        grid.setSpacing(10)
        
        # Define Labels
        self.lbl_deposit = self._create_info_label(language_manager.get_text('deposit'))
        self.val_deposit = self._create_value_label("0")
        
        self.lbl_purchase = self._create_info_label(language_manager.get_text('total_purchase', 'Total Purchase'))
        self.val_purchase = self._create_value_label("0")
        
        self.lbl_eval = self._create_info_label(language_manager.get_text('total_eval', 'Total Eval'))
        self.val_eval = self._create_value_label("0")
        
        self.lbl_pnl = self._create_info_label(language_manager.get_text('pnl'))
        self.val_pnl = self._create_value_label("0")
        
        self.lbl_return = self._create_info_label(language_manager.get_text('total_return', 'Return %'))
        self.val_return = self._create_value_label("0.00%")
        
        self.lbl_asset = self._create_info_label(language_manager.get_text('total_asset'))
        self.val_asset = self._create_value_label("0")
        
        # Layout (Row 1)
        grid.addWidget(self.lbl_deposit, 0, 0); grid.addWidget(self.val_deposit, 1, 0)
        grid.addWidget(self.lbl_purchase, 0, 1); grid.addWidget(self.val_purchase, 1, 1)
        grid.addWidget(self.lbl_eval, 0, 2); grid.addWidget(self.val_eval, 1, 2)
        
        # Layout (Row 2)
        grid.addWidget(self.lbl_pnl, 2, 0); grid.addWidget(self.val_pnl, 3, 0)
        grid.addWidget(self.lbl_return, 2, 1); grid.addWidget(self.val_return, 3, 1)
        grid.addWidget(self.lbl_asset, 2, 2); grid.addWidget(self.val_asset, 3, 2)
        
        summary_layout.addLayout(grid)
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

    def update_account_summary(self, total_asset, deposit, total_pnl, total_purchase, total_eval, total_return):
        def fmt(val):
            return f"{val:,.0f}" if val else "0"
            
        self.val_deposit.setText(fmt(deposit))
        self.val_purchase.setText(fmt(total_purchase))
        self.val_eval.setText(fmt(total_eval))
        self.val_asset.setText(fmt(total_asset))
        
        # PnL
        self.val_pnl.setText(fmt(total_pnl))
        if total_pnl > 0:
            self.val_pnl.setStyleSheet("color: #ff5252; font-weight: bold; font-size: 13px;")
        elif total_pnl < 0:
            self.val_pnl.setStyleSheet("color: #448aff; font-weight: bold; font-size: 13px;")
        else:
            self.val_pnl.setStyleSheet("color: white; font-weight: bold; font-size: 13px;")
            
        # Return Rate
        self.val_return.setText(f"{total_return:+.2f}%")
        if total_return > 0:
            self.val_return.setStyleSheet("color: #ff5252; font-weight: bold; font-size: 13px;")
        elif total_return < 0:
            self.val_return.setStyleSheet("color: #448aff; font-weight: bold; font-size: 13px;")
        else:
            self.val_return.setStyleSheet("color: white; font-weight: bold; font-size: 13px;")

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

    def _create_info_label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #888; font-size: 11px;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return lbl

    def _create_value_label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("color: white; font-size: 13px; font-weight: bold;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return lbl
