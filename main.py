import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from app.window import MainWindow
from app.settings import GLOBAL_STYLESHEET

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(GLOBAL_STYLESHEET)
    app.setWindowIcon(QIcon("assets/icon.png"))

    window = MainWindow()
    window.showMaximized()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()

