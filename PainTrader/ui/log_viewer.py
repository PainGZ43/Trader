import logging
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit, QComboBox, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QFont

class LogSignalHandler(logging.Handler, QObject):
    """
    Custom logging handler that emits a signal when a log record is created.
    """
    log_signal = pyqtSignal(str, int) # message, levelno

    def __init__(self):
        super().__init__()
        QObject.__init__(self)

    def emit(self, record):
        msg = self.format(record)
        self.log_signal.emit(msg, record.levelno)

class LogViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setup_logging()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Filter Bar
        filter_layout = QHBoxLayout()
        self.level_combo = QComboBox()
        self.level_combo.addItems(["ALL", "INFO", "WARNING", "ERROR"])
        self.level_combo.currentTextChanged.connect(self.filter_logs)
        
        filter_layout.addWidget(QLabel("Log Level:"))
        filter_layout.addWidget(self.level_combo)
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)

        # Log Text Area
        self.text_edit = QPlainTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setFont(QFont("Consolas", 9))
        self.text_edit.setStyleSheet("background-color: #1e1e1e; color: #dcdcdc;")
        layout.addWidget(self.text_edit)

    def setup_logging(self):
        self.handler = LogSignalHandler()
        self.handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s", datefmt='%H:%M:%S'))
        self.handler.log_signal.connect(self.append_log)
        
        # Attach to root logger to capture everything
        logging.getLogger().addHandler(self.handler)

    def append_log(self, msg, levelno):
        # Color coding based on level
        color = "#dcdcdc" # Default (INFO)
        if levelno >= logging.ERROR:
            color = "#ff6b6b" # Red
        elif levelno >= logging.WARNING:
            color = "#feca57" # Yellow
        elif levelno == logging.DEBUG:
            color = "#54a0ff" # Blue

        # Simple HTML formatting for color
        html_msg = f'<span style="color:{color};">{msg}</span>'
        self.text_edit.appendHtml(html_msg)

    def filter_logs(self, text):
        # Note: This is a visual filter for future logs or we could implement a model-based filter.
        # For now, we just change the handler level.
        level_map = {
            "ALL": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR
        }
        self.handler.setLevel(level_map.get(text, logging.INFO))
