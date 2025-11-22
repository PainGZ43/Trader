import PyInstaller.__main__
import os

def build():
    print("Building Executable...")
    
    PyInstaller.__main__.run([
        'main.py',
        '--name=KiwoomAITrader',
        '--onefile',
        '--windowed',
        '--icon=NONE', # Add icon path if available
        '--add-data=ui/styles.qss;ui',
        '--hidden-import=pyqtgraph',
        '--hidden-import=pandas',
        '--hidden-import=sqlalchemy',
        '--hidden-import=qasync',
        '--hidden-import=dotenv',
        '--clean',
    ])
    
    print("Build Complete! Check 'dist' folder.")

if __name__ == "__main__":
    build()
