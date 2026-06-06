# Import torch first to resolve Windows DLL initialization conflict with PyQt5 (WinError 1114)
try:
    import torch
except ImportError:
    pass

import sys
import os
from PyQt5.QtWidgets import QApplication
from gui.main_window import MainWindow

def setup_directories():
    """
    Creates necessary directories if they do not exist.
    """
    dirs = [
        "data",
        "data/images",
        "data/videos",
        "models",
        "output",
        "output/logs",
        "output/plates"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def main():
    # Setup folders
    setup_directories()

    # Initialize PyQt application
    app = QApplication(sys.argv)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start the event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
