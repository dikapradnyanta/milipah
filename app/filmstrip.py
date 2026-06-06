"""
filmstrip.py — Horizontal thumbnail widget.
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import pyqtSignal, Qt, QSize
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QScrollArea, QLabel, QVBoxLayout

from app.settings import COLORS, SUBFOLDER_COLORS

THUMB_DISPLAY_SIZE = 120


class ThumbnailCell(QWidget):
    """A single thumbnail in the filmstrip."""
    
    clicked = pyqtSignal(int) # emits the index of this cell

    def __init__(self, index: int, parent=None):
        super().__init__(parent)
        self.index = index
        self.path: Path | None = None
        self.assignment: str | None = None
        self.assignment_color: str | None = None
        self.is_active = False
        
        self.setFixedSize(THUMB_DISPLAY_SIZE, THUMB_DISPLAY_SIZE)
        
        self.image_label = QLabel(self)
        self.image_label.setFixedSize(THUMB_DISPLAY_SIZE - 4, THUMB_DISPLAY_SIZE - 4)
        self.image_label.move(2, 2)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet(f"background-color: {COLORS['Surface']};")
        
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_data(self, path: Path):
        self.path = path
        # Show a placeholder initially
        self.image_label.setText(path.suffix[1:].upper())

    def set_thumbnail_image(self, pixmap: QPixmap):
        """Called when background generation finishes."""
        scaled = pixmap.scaled(
            self.image_label.size(), 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        self.image_label.setPixmap(scaled)

    def set_assignment(self, assignment: str | None, color: str | None):
        self.assignment = assignment
        self.assignment_color = color
        self.update() # trigger paintEvent

    def set_active(self, active: bool):
        self.is_active = active
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.index)
            
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw active border
        if self.is_active:
            pen = QPen(QColor(COLORS['TextPrimary']), 2)
            painter.setPen(pen)
            painter.drawRect(1, 1, self.width() - 2, self.height() - 2)
            
        # Draw assignment badge
        if self.assignment:
            if self.assignment == 'skip':
                painter.fillRect(0, 0, self.width(), self.height(), QColor(0, 0, 0, 150))
                painter.setPen(QPen(QColor(COLORS['TextMuted'])))
                painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "SKIPPED")
            else:
                if self.assignment_color:
                    badge_size = 16
                    painter.setBrush(QColor(self.assignment_color))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawEllipse(self.width() - badge_size - 4, 4, badge_size, badge_size)


class FilmstripWidget(QScrollArea):
    """Horizontal scroll area containing ThumbnailCells."""
    
    cell_clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(THUMB_DISPLAY_SIZE + 24) # padding for scrollbar
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.container = QWidget()
        self.layout = QHBoxLayout(self.container)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(5)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.setWidget(self.container)
        self.cells: list[ThumbnailCell] = []
        
    def populate(self, paths: list[Path]):
        """Create a cell for every photo. (For 50k this might be heavy, but QWidgets are quite light)."""
        self.clear()
        for i, path in enumerate(paths):
            cell = ThumbnailCell(i)
            cell.set_data(path)
            cell.clicked.connect(self.cell_clicked.emit)
            self.layout.addWidget(cell)
            self.cells.append(cell)

    def clear(self):
        # Remove all existing widgets from layout
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.cells.clear()

    def update_cell_image(self, index: int, pixmap: QPixmap):
        if 0 <= index < len(self.cells):
            self.cells[index].set_thumbnail_image(pixmap)

    def update_cell_assignment(self, index: int, assignment: str | None, color: str | None):
        if 0 <= index < len(self.cells):
            self.cells[index].set_assignment(assignment, color)

    def set_active_index(self, index: int):
        for i, cell in enumerate(self.cells):
            cell.set_active(i == index)
            
        if 0 <= index < len(self.cells):
            # Auto-scroll to make it visible
            self.ensureWidgetVisible(self.cells[index], 50, 0)
