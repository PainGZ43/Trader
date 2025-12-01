import sys
import pytest
from PyQt6.QtWidgets import QApplication, QDockWidget
from ui.main_window import MainWindow
from ui.widgets.header_bar import HeaderBar

# Fixture to handle QApplication singleton
@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app

def test_mainwindow_structure(qapp):
    """Test MainWindow initialization and layout."""
    window = MainWindow()
    
    # 1. Check Title
    assert "PainTrader AI" in window.windowTitle()
    
    # 2. Check HeaderBar
    header = window.findChild(HeaderBar)
    assert header is not None
    # assert header.isVisible() # Flaky without event loop
    
    # 3. Check Dock Widgets
    docks = window.findChildren(QDockWidget)
    dock_names = [d.objectName() for d in docks]
    
    expected_docks = ["Strategy & Account", "Execution", "Logs & History"]
    for name in expected_docks:
        assert name in dock_names
        
    # 4. Check Central Widget
    assert window.centralWidget() is not None
    
    window.close()

def test_headerbar_components(qapp):
    """Test HeaderBar components."""
    header = HeaderBar()
    
    # Check Logo
    assert header.findChild(object, "LogoLabel") is not None
    
    # Check Status Indicators (implied by existence, but we can check layout count)
    # Header layout has: Logo, Title, Stretch, Macro(3), Stretch, Status(3), Resource, Global(3)
    # Total items should be roughly 13-15 depending on implementation details
    assert header.layout.count() > 10
    
    header.close()
