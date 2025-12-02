from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, 
    QPushButton, QComboBox, QLineEdit, QFormLayout, QGroupBox,
    QListWidgetItem, QMessageBox, QInputDialog
)
from PyQt6.QtCore import Qt
from core.config import config
from core.language import language_manager

class ChartSettingsDialog(QDialog):
    def __init__(self, parent=None, current_indicators=None):
        super().__init__(parent)
        self.setWindowTitle("Chart Indicators")
        self.resize(600, 400)
        
        self.current_indicators = current_indicators or [] # List of dicts
        self.available_indicators = {
            "SMA": {"timeperiod": 20, "color": "#ff9f43"},
            "EMA": {"timeperiod": 20, "color": "#feca57"},
            "RSI": {"timeperiod": 14, "color": "#54a0ff"},
            "MACD": {"fastperiod": 12, "slowperiod": 26, "signalperiod": 9, "color": "#ff6b6b"},
            "BBANDS": {"timeperiod": 20, "nbdevup": 2, "nbdevdn": 2, "color": "#ff9f43"},
            "STOCH": {"fastk_period": 5, "slowk_period": 3, "slowd_period": 3, "color": "#1dd1a1"}
        }
        
        self.init_ui()
        self.load_templates()

    def init_ui(self):
        layout = QHBoxLayout(self)
        
        # 1. Left Panel: Available Indicators
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Available Indicators"))
        
        self.list_available = QListWidget()
        self.list_available.addItems(self.available_indicators.keys())
        self.list_available.currentItemChanged.connect(self.on_available_selected)
        left_layout.addWidget(self.list_available)
        
        btn_add = QPushButton("Add ->")
        btn_add.clicked.connect(self.add_indicator)
        left_layout.addWidget(btn_add)
        
        layout.addLayout(left_layout, 1)
        
        # 2. Middle Panel: Parameters
        self.param_group = QGroupBox("Parameters")
        self.param_layout = QFormLayout()
        self.param_group.setLayout(self.param_layout)
        self.param_inputs = {}
        
        layout.addWidget(self.param_group, 1)
        
        # 3. Right Panel: Active Indicators
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Active Indicators"))
        
        self.list_active = QListWidget()
        self.refresh_active_list()
        right_layout.addWidget(self.list_active)
        
        btn_remove = QPushButton("Remove")
        btn_remove.clicked.connect(self.remove_indicator)
        right_layout.addWidget(btn_remove)
        
        # Templates
        template_layout = QHBoxLayout()
        self.combo_templates = QComboBox()
        self.combo_templates.currentIndexChanged.connect(self.on_template_selected)
        
        btn_save_tpl = QPushButton("Save Tpl")
        btn_save_tpl.clicked.connect(self.save_template)
        
        template_layout.addWidget(self.combo_templates)
        template_layout.addWidget(btn_save_tpl)
        
        right_layout.addLayout(template_layout)
        
        # Dialog Buttons
        btn_box = QHBoxLayout()
        btn_apply = QPushButton("Apply")
        btn_apply.clicked.connect(self.accept)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        
        btn_box.addStretch()
        btn_box.addWidget(btn_apply)
        btn_box.addWidget(btn_cancel)
        
        right_layout.addLayout(btn_box)
        
        layout.addLayout(right_layout, 1)

    def on_available_selected(self, current, previous):
        if not current: return
        
        name = current.text()
        defaults = self.available_indicators.get(name, {})
        
        # Clear existing inputs
        for i in reversed(range(self.param_layout.count())):
            self.param_layout.itemAt(i).widget().setParent(None)
        self.param_inputs = {}
        
        # Create inputs
        for key, val in defaults.items():
            lbl = QLabel(key)
            inp = QLineEdit(str(val))
            self.param_layout.addRow(lbl, inp)
            self.param_inputs[key] = inp

    def add_indicator(self):
        item = self.list_available.currentItem()
        if not item: return
        
        name = item.text()
        params = {}
        for key, inp in self.param_inputs.items():
            val = inp.text()
            # Try convert to int/float
            try:
                if "." in val:
                    params[key] = float(val)
                else:
                    params[key] = int(val)
            except:
                params[key] = val
                
        indicator = {"name": name, "params": params}
        self.current_indicators.append(indicator)
        self.refresh_active_list()

    def remove_indicator(self):
        row = self.list_active.currentRow()
        if row >= 0:
            del self.current_indicators[row]
            self.refresh_active_list()

    def refresh_active_list(self):
        self.list_active.clear()
        for ind in self.current_indicators:
            name = ind["name"]
            params = ind["params"]
            # Format params for display
            param_str = ", ".join([f"{k}:{v}" for k, v in params.items() if k != "color"])
            self.list_active.addItem(f"{name} ({param_str})")

    def get_indicators(self):
        return self.current_indicators

    def load_templates(self):
        templates = config.get("chart_templates", {})
        self.combo_templates.clear()
        self.combo_templates.addItem("Select Template...")
        for name in templates.keys():
            self.combo_templates.addItem(name)

    def on_template_selected(self):
        name = self.combo_templates.currentText()
        if name == "Select Template...": return
        
        templates = config.get("chart_templates", {})
        if name in templates:
            self.current_indicators = templates[name]
            self.refresh_active_list()

    def save_template(self):
        name, ok = QInputDialog.getText(self, "Save Template", "Template Name:")
        if ok and name:
            templates = config.get("chart_templates", {})
            templates[name] = self.current_indicators
            config.save("chart_templates", templates)
            self.load_templates()
            self.combo_templates.setCurrentText(name)
