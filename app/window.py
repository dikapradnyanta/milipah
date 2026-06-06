"""
window.py — MainWindow holding the QStackedWidget shell.
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import QMainWindow, QStackedWidget, QMessageBox

from app.settings import DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT
from core.session import SessionManager


class MainWindow(QMainWindow):
    """
    Main application shell. Switches between SetupPanel and SortPanel.
    Handles global session state.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Milipah")
        
        # Don't force a large hardcoded resize which causes "zoom" on smaller screens
        self.setMinimumSize(800, 600)
        
        self.session: SessionManager | None = None
        
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        # Lazy import to avoid circular dependencies
        from app.setup_panel import SetupPanel
        from app.sort_panel import SortPanel
        
        self.setup_panel = SetupPanel(self)
        self.sort_panel = SortPanel(self)
        
        self.stack.addWidget(self.setup_panel)
        self.stack.addWidget(self.sort_panel)
        
        self.setup_panel.session_ready.connect(self.start_sorting)
        self.sort_panel.session_ended.connect(self.return_to_setup)

    def start_sorting(self, source_folder: Path, subfolders: list[dict]):
        """Called when SetupPanel is done."""
        
        # Check for existing session
        if SessionManager.detect_existing_session(source_folder):
            reply = QMessageBox.question(
                self,
                "Sesi Ditemukan",
                f"Sesi sebelumnya untuk folder ini ditemukan.\nLanjutkan sesi?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            self.session = SessionManager(source_folder)
            self.session.open()
            
            if reply == QMessageBox.StandardButton.Yes:
                # Resume: pass existing assignments down
                pass
            else:
                # Start fresh
                self.session.clear_session()
                self.session.init_session()
                self.session.save_subfolders(subfolders)
        else:
            self.session = SessionManager(source_folder)
            self.session.open()
            self.session.init_session()
            self.session.save_subfolders(subfolders)

        self.sort_panel.load_session(self.session, source_folder)
        self.stack.setCurrentWidget(self.sort_panel)

    def return_to_setup(self):
        """Called when SortPanel finishes Apply or User backs out."""
        if self.session:
            self.session.close()
            self.session = None
            
        self.setup_panel.reset()
        self.stack.setCurrentWidget(self.setup_panel)
        
    def keyPressEvent(self, event):
        # Forward key events to active panel if it handles them
        active_widget = self.stack.currentWidget()
        if hasattr(active_widget, 'handle_keypress'):
            if active_widget.handle_keypress(event):
                return
        super().keyPressEvent(event)
