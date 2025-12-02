from PyQt6.QtWidgets import QComboBox, QCompleter
from PyQt6.QtCore import Qt, QSortFilterProxyModel, QStringListModel
from core.database import db
import asyncio
from qasync import asyncSlot

class SymbolSearchWidget(QComboBox):
    """
    A ComboBox that allows searching by Code or Name.
    Loads data from DB asynchronously.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        
        # Data storage
        self.codes = []
        self.names = []
        self.items = [] # Format: "Name (Code)"
        self.code_map = {} # "Name (Code)" -> Code
        
        # Initialize
        self.load_data()
        
        # Setup Completer
        self.completer = QCompleter(self)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.setCompleter(self.completer)

    @asyncSlot()
    async def load_data(self):
        """Load codes from DB."""
        try:
            # Check if DB is connected, if not, maybe wait or skip
            # Assuming DB is initialized by main app
            query = "SELECT code, name, market FROM market_code ORDER BY name"
            rows = await db.fetch_all(query)
            
            self.items = []
            self.code_map = {}
            
            for row in rows:
                code = row['code']
                name = row['name']
                market = row['market']
                
                display_text = f"{name} ({code})"
                self.items.append(display_text)
                self.code_map[display_text] = code
                
            # Update Model
            self.addItems(self.items)
            
            # Update Completer Model
            self.completer.setModel(self.model())
            
        except Exception as e:
            print(f"SymbolSearchWidget Load Error: {e}")

    def get_current_code(self):
        """Return the selected code."""
        text = self.currentText()
        # If user typed exact code
        if text.isdigit() and len(text) == 6:
            return text
            
        # If selected from list
        return self.code_map.get(text, "")

    def set_code(self, code):
        """Set selection by code."""
        # Find item with this code
        for text, c in self.code_map.items():
            if c == code:
                self.setCurrentText(text)
                return
