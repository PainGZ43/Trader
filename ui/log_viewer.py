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
import logging
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit, QComboBox, QHBoxLayout, QLabel, QLineEdit, QCheckBox, QPushButton
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
        filter_layout.addWidget(QLabel("Level:"))
        filter_layout.addWidget(self.level_combo)
        
        self.chk_auto_scroll = QCheckBox("Auto Scroll")
        self.chk_auto_scroll.setChecked(True)
        self.chk_auto_scroll.setStyleSheet("color: #dcdcdc;")
        filter_layout.addWidget(self.chk_auto_scroll)
        
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
        
        if self.chk_auto_scroll.isChecked():
            self.text_edit.verticalScrollBar().setValue(self.text_edit.verticalScrollBar().maximum())

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

    def search_logs(self, text):
        # Basic highlighting or filtering could be complex in QPlainTextEdit without a model.
        # For this version, we will just highlight the text if found.
        if not text:
            return
            
        cursor = self.text_edit.textCursor()
        # Reset selection
        cursor.clearSelection()
        self.text_edit.setTextCursor(cursor)
        
        if self.text_edit.find(text):
            # Found
            pass
        else:
            # Not found, maybe reset cursor to start and search again
            self.text_edit.moveCursor(self.text_edit.textCursor().MoveOperation.Start)
            if self.text_edit.find(text):
                pass

    def save_logs_to_file(self):
        from PyQt6.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getSaveFileName(self, "Save Log File", "", "Text Files (*.txt);;All Files (*)")
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.text_edit.toPlainText())
            except Exception as e:
                print(f"Failed to save logs: {e}")
