import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from app.window import MainWindow
from app.settings import GLOBAL_STYLESHEET

import os

def get_base_path():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(GLOBAL_STYLESHEET)
    
    icon_path = os.path.join(get_base_path(), "assets", "setup_icon.ico")
    app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()
    window.showMaximized()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()

