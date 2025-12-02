from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QPushButton, QLineEdit, QTableWidget, QTableWidgetItem, 
    QHeaderView, QMenu, QInputDialog, QMessageBox, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData
from PyQt6.QtGui import QColor, QDrag
from core.config import config
from core.language import language_manager
from core.event_bus import event_bus

class WatchlistWidget(QWidget):
    """
    Widget for managing and displaying watchlists (interested stocks).
    Supports multiple groups, drag & drop reordering, and real-time updates.
    """
    symbol_selected = pyqtSignal(str) # Emits symbol code when clicked

    def __init__(self, parent=None):
        super().__init__(parent)
        self.groups = []
        self.active_group_idx = 0
        self.init_ui()
        self.load_settings()
        
        # Subscribe to real-time data
        event_bus.subscribe("market.data.realtime", self.on_realtime_data)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # 1. Top Toolbar (Group Control)
        top_layout = QHBoxLayout()
        top_layout.setSpacing(5)
        
        self.combo_group = QComboBox()
        self.combo_group.currentIndexChanged.connect(self.on_group_changed)
        
        btn_add_group = QPushButton("+")
        btn_add_group.setFixedWidth(25)
        btn_add_group.setToolTip("Add Group")
        btn_add_group.clicked.connect(self.add_group)
        
        btn_edit_group = QPushButton("✎")
        btn_edit_group.setFixedWidth(25)
        btn_edit_group.setToolTip("Rename Group")
        btn_edit_group.clicked.connect(self.rename_group)
        
        btn_del_group = QPushButton("-")
        btn_del_group.setFixedWidth(25)
        btn_del_group.setToolTip("Delete Group")
        btn_del_group.clicked.connect(self.delete_group)
        
        top_layout.addWidget(self.combo_group, 1)
        top_layout.addWidget(btn_add_group)
        top_layout.addWidget(btn_edit_group)
        top_layout.addWidget(btn_del_group)
        
        layout.addLayout(top_layout)
        
        # 2. Add Symbol Bar
        input_layout = QHBoxLayout()
        self.input_symbol = QLineEdit()
        self.input_symbol.setPlaceholderText("Code or Name...")
        self.input_symbol.returnPressed.connect(self.add_symbol)
        
        btn_add_sym = QPushButton("Add")
        btn_add_sym.clicked.connect(self.add_symbol)
        
        input_layout.addWidget(self.input_symbol)
        input_layout.addWidget(btn_add_sym)
        
        layout.addLayout(input_layout)
        
        # 3. Watchlist Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Symbol", "Price", "Chg", "Vol"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        # Drag & Drop
        self.table.setDragEnabled(True)
        self.table.setAcceptDrops(True)
        self.table.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.table.setDropIndicatorShown(True)
        
        self.table.cellClicked.connect(self.on_cell_clicked)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
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
        
        layout.addWidget(self.table)

    def load_settings(self):
        """Load watchlist groups from settings."""
        watchlist_data = config.get("watchlist", {})
        self.groups = watchlist_data.get("groups", [])
        
        if not self.groups:
            # Default Group
            self.groups = [{"name": "Default", "codes": ["005930", "000660"]}]
            
        self.refresh_combo()
        
        active_idx = watchlist_data.get("active_group_idx", 0)
        if 0 <= active_idx < len(self.groups):
            self.combo_group.setCurrentIndex(active_idx)
        else:
            self.combo_group.setCurrentIndex(0)
            
        # Defer initial refresh to ensure EventBus has a loop
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, self.refresh_table)

    def save_settings(self):
        """Save current groups to settings."""
        data = {
            "groups": self.groups,
            "active_group_idx": self.combo_group.currentIndex()
        }
        config.save("watchlist", data)

    def refresh_combo(self):
        self.combo_group.blockSignals(True)
        self.combo_group.clear()
        for g in self.groups:
            self.combo_group.addItem(g["name"])
        self.combo_group.blockSignals(False)

    def refresh_table(self):
        self.table.setRowCount(0)
        idx = self.combo_group.currentIndex()
        if idx < 0 or idx >= len(self.groups):
            return
            
        codes = self.groups[idx]["codes"]
        self.table.setRowCount(len(codes))
        
        for i, code in enumerate(codes):
            # Initial Row Setup
            self.table.setItem(i, 0, QTableWidgetItem(code))
            self.table.setItem(i, 1, QTableWidgetItem("-"))
            self.table.setItem(i, 2, QTableWidgetItem("-"))
            self.table.setItem(i, 3, QTableWidgetItem("-"))
            
        # Request Real-time Data Subscription for these codes
        event_bus.publish("watchlist.updated", {"codes": codes})

    def on_group_changed(self, index):
        self.active_group_idx = index
        self.refresh_table()
        self.save_settings()

    def add_group(self):
        name, ok = QInputDialog.getText(self, "Add Group", "Group Name:")
        if ok and name:
            self.groups.append({"name": name, "codes": []})
            self.refresh_combo()
            self.combo_group.setCurrentIndex(len(self.groups) - 1)
            self.save_settings()

    def rename_group(self):
        idx = self.combo_group.currentIndex()
        if idx < 0: return
        
        old_name = self.groups[idx]["name"]
        name, ok = QInputDialog.getText(self, "Rename Group", "New Name:", text=old_name)
        if ok and name:
            self.groups[idx]["name"] = name
            self.refresh_combo()
            self.combo_group.setCurrentIndex(idx)
            self.save_settings()

    def delete_group(self):
        idx = self.combo_group.currentIndex()
        if idx < 0: return
        
        reply = QMessageBox.question(self, "Delete Group", f"Delete '{self.groups[idx]['name']}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            del self.groups[idx]
            if not self.groups:
                self.groups.append({"name": "Default", "codes": []})
            self.refresh_combo()
            self.save_settings()

    def add_symbol(self):
        code = self.input_symbol.text().strip()
        if not code: return
        
        # TODO: Validate code or convert name to code
        
        idx = self.combo_group.currentIndex()
        if idx < 0: return
        
        if code not in self.groups[idx]["codes"]:
            self.groups[idx]["codes"].append(code)
            self.refresh_table()
            self.save_settings()
            self.input_symbol.clear()

    def on_cell_clicked(self, row, col):
        item = self.table.item(row, 0)
        if item:
            code = item.text()
            self.symbol_selected.emit(code)
            # Publish event to change global symbol
            event_bus.publish("symbol.changed", code)

    def show_context_menu(self, pos):
        menu = QMenu()
        del_action = menu.addAction("Delete Symbol")
        action = menu.exec(self.table.mapToGlobal(pos))
        
        if action == del_action:
            row = self.table.currentRow()
            if row >= 0:
                idx = self.combo_group.currentIndex()
                del self.groups[idx]["codes"][row]
                self.refresh_table()
                self.save_settings()

    def on_realtime_data(self, data):
        """
        Update table with real-time data.
        data: dict with 'code', 'price', 'change', 'change_pct', 'volume'
        """
        # This is inefficient for large lists, optimization needed later (map code -> row)
        code = data.get('code')
        if not code: return
        
        # Find row
        # Optimization: Maintain a dict mapping code -> row index?
        # But row index changes on drag/drop.
        # Just search for now (watchlist is small < 100)
        
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.text() == code:
                price = data.get('price', 0)
                change = data.get('change', 0)
                pct = data.get('change_pct', 0)
                vol = data.get('volume', 0)
                
                self.table.setItem(row, 1, QTableWidgetItem(f"{price:,}"))
                
                # Color
                color = QColor("white")
                if change > 0: color = QColor("#ff6b6b")
                elif change < 0: color = QColor("#54a0ff")
                
                change_item = QTableWidgetItem(f"{change} ({pct}%)")
                change_item.setForeground(color)
                self.table.setItem(row, 2, change_item)
                
                self.table.setItem(row, 3, QTableWidgetItem(f"{vol:,}"))
                break
