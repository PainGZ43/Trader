import PyInstaller.__main__
import os
import shutil

# Define paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST_DIR = os.path.join(BASE_DIR, "dist")
BUILD_DIR = os.path.join(BASE_DIR, "build")
WORK_DIR = BASE_DIR

# Clean previous builds
if os.path.exists(DIST_DIR):
    shutil.rmtree(DIST_DIR)
if os.path.exists(BUILD_DIR):
    shutil.rmtree(BUILD_DIR)

# PyInstaller Arguments
args = [
    'main.py',                      # Entry point
    '--name=PainTrader',            # Executable name
    '--noconfirm',                  # Overwrite output
    '--windowed',                   # No console window (GUI mode)
    '--clean',                      # Clean cache
    
    # Hidden Imports (Dependencies that might be missed)
    '--hidden-import=PyQt6',
    '--hidden-import=PyQt6.QtCore',
    '--hidden-import=PyQt6.QtGui',
    '--hidden-import=PyQt6.QtWidgets',
    '--hidden-import=pandas',
    '--hidden-import=numpy',
    '--hidden-import=aiosqlite',
    '--hidden-import=aiohttp',
    '--hidden-import=pyqtgraph',
    
    # Exclude conflicting Qt bindings
    '--exclude-module=PyQt5',
    '--exclude-module=PySide2',
    '--exclude-module=PySide6',
    
    # Data Files (if any)
    # '--add-data=resources;resources', 
    
    # Icon (if available)
    # '--icon=resources/icon.ico',
]

print("Starting PyInstaller Build...")
print(f"Base Dir: {BASE_DIR}")

# Run PyInstaller
PyInstaller.__main__.run(args)

print("Build Complete.")
print(f"Executable located at: {os.path.join(DIST_DIR, 'PainTrader', 'PainTrader.exe')}")
