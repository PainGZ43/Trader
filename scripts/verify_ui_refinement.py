import sys
import os
import unittest
from PyQt6.QtWidgets import QApplication, QTableWidgetItem
from PyQt6.QtCore import Qt

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.widgets.order_book_widget import OrderBookWidget

class TestUIRefinement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create QApplication if it doesn't exist
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

    def test_order_book_delegate_logic(self):
        print("\n[TEST] Testing OrderBookWidget Delegate Logic...")
        widget = OrderBookWidget()
        
        # Sample Data
        asks = [(1000, 10), (1010, 20), (1020, 5)]
        bids = [(990, 15), (980, 30), (970, 10)]
        
        widget.update_orderbook(asks, bids)
        
        # Max Vol is 30 (from bids)
        # Check Ask Row (Row 9 should be lowest ask: 1000, vol 10)
        # Ratio = 10 / 30 = 0.333
        
        # In update_orderbook:
        # Asks are filled in rows 0-9.
        # Lowest ask (1000) is at row 9.
        
        item = widget.table.item(9, 0) # Ask Vol Column
        self.assertIsNotNone(item)
        ratio = item.data(Qt.ItemDataRole.UserRole)
        print(f"Row 9 (Ask 1000) Ratio: {ratio}")
        self.assertAlmostEqual(ratio, 10/30, places=2)
        
        # Check Bid Row (Row 10 should be highest bid: 990, vol 15)
        # Ratio = 15 / 30 = 0.5
        item = widget.table.item(10, 2) # Bid Vol Column
        self.assertIsNotNone(item)
        ratio = item.data(Qt.ItemDataRole.UserRole)
        print(f"Row 10 (Bid 990) Ratio: {ratio}")
        self.assertAlmostEqual(ratio, 15/30, places=2)
        
        print("OrderBookDelegate logic verified.")

if __name__ == '__main__':
    unittest.main()
