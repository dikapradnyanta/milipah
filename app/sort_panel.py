"""
sort_panel.py — The main application view for the sorting process.
"""

from __future__ import annotations

import os
from pathlib import Path

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QPixmap, QShortcut, QKeySequence
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFrame, QMessageBox, QLineEdit
)

from app.settings import COLORS, THUMB_SLIDING_WINDOW
from app.filmstrip import FilmstripWidget
from app.apply_dialog import ApplyDialog
from core.scanner import FolderScanner
from core.thumbnail import ThumbnailManager
from core.session import SessionManager


class SortPanel(QWidget):
    """
    Main sorting view.
    Layout: 
      Left: Subfolder buttons & Undo
      Center: Main Preview
      Right: Metadata
      Bottom: Filmstrip & Status
    """
    
    session_ended = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.session: SessionManager | None = None
        self.source_folder: Path | None = None
        
        self.paths: list[Path] = []
        self.filtered_indices: list[int] = []  # Maps filtered position to true absolute index
        self.current_idx: int = -1             # Absolute index (0 to len(paths)-1)
        
        self.subfolders: list[dict] = []
        self.assignments: dict[str, str | None] = {}
        self.undo_stack: list[tuple[str, str | None]] = [] # list of (file_path, previous_assignment)
        
        self.thumb_manager: ThumbnailManager | None = None
        
        self.filter_mode = "all" # "all", "unassigned", "skip", or subfolder name
        
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- Top Area (Main Content) ---
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(0)
        
        # 1. Left Sidebar (Controls)
        self.left_sidebar = QFrame()
        self.left_sidebar.setFixedWidth(200)
        self.left_sidebar.setStyleSheet(f"background-color: {COLORS['Surface']}; border-right: 1px solid {COLORS['Border']};")
        left_layout = QVBoxLayout(self.left_sidebar)
        left_layout.setContentsMargins(15, 20, 15, 20)
        
        lbl_assign = QLabel("ASSIGNMENT")
        lbl_assign.setStyleSheet(f"color: {COLORS['TextSecondary']}; font-weight: bold; font-size: 12px; border: none;")
        left_layout.addWidget(lbl_assign)
        
        self.buttons_layout = QVBoxLayout()
        left_layout.addLayout(self.buttons_layout)
        
        left_layout.addStretch()
        
        # Add new subfolder UI
        self.add_sub_layout = QHBoxLayout()
        self.input_subfolder = QLineEdit()
        self.input_subfolder.setPlaceholderText("Subfolder baru...")
        self.input_subfolder.setStyleSheet(f"background-color: {COLORS['Background']}; color: {COLORS['TextPrimary']}; padding: 5px;")
        self.btn_add_subfolder = QPushButton("+")
        self.btn_add_subfolder.setFixedWidth(30)
        self.btn_add_subfolder.clicked.connect(self.add_subfolder)
        self.input_subfolder.returnPressed.connect(self.add_subfolder)
        
        self.add_sub_layout.addWidget(self.input_subfolder)
        self.add_sub_layout.addWidget(self.btn_add_subfolder)
        left_layout.addLayout(self.add_sub_layout)
        
        # Spacer before skip/undo
        spacer = QWidget()
        spacer.setFixedHeight(10)
        left_layout.addWidget(spacer)
        
        self.btn_skip = QPushButton("Skip (S)")
        self.btn_skip.clicked.connect(self.action_skip)
        left_layout.addWidget(self.btn_skip)
        
        self.btn_undo = QPushButton("Undo (Z)")
        self.btn_undo.clicked.connect(self.action_undo)
        left_layout.addWidget(self.btn_undo)
        
        top_layout.addWidget(self.left_sidebar)
        
        # 2. Center (Preview)
        self.preview_container = QFrame()
        self.preview_container.setStyleSheet(f"background-color: {COLORS['Background']}; border: none;")
        preview_layout = QVBoxLayout(self.preview_container)
        
        # Loading indicator for scanner
        self.lbl_loading = QLabel("Mencari foto...")
        self.lbl_loading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_loading.setStyleSheet("font-size: 18px;")
        preview_layout.addWidget(self.lbl_loading)
        
        self.lbl_preview = QLabel()
        self.lbl_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_preview.hide()
        preview_layout.addWidget(self.lbl_preview, stretch=1)
        
        # Colored line to indicate assignment status
        self.status_line = QFrame()
        self.status_line.setFixedHeight(6)
        self.status_line.setStyleSheet(f"QFrame {{ background-color: {COLORS['Border']}; }}")
        preview_layout.addWidget(self.status_line)
        
        top_layout.addWidget(self.preview_container, stretch=1)
        
        # 3. Right Sidebar (Metadata & Apply)
        self.right_sidebar = QFrame()
        self.right_sidebar.setFixedWidth(220)
        self.right_sidebar.setStyleSheet(f"background-color: {COLORS['Surface']}; border-left: 1px solid {COLORS['Border']};")
        right_layout = QVBoxLayout(self.right_sidebar)
        right_layout.setContentsMargins(15, 20, 15, 20)
        
        self.btn_apply = QPushButton("Apply & Lanjut")
        self.btn_apply.setFixedHeight(50)
        self.btn_apply.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['AccentGreen']};
                color: #141414;
                font-weight: bold;
                font-size: 14px;
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: #6edcb6;
            }}
        """)
        self.btn_apply.clicked.connect(self.show_apply_dialog)
        right_layout.addWidget(self.btn_apply)
        
        lbl_meta = QLabel("METADATA")
        lbl_meta.setStyleSheet(f"color: {COLORS['TextSecondary']}; font-weight: bold; font-size: 12px; border: none; margin-top: 20px;")
        right_layout.addWidget(lbl_meta)
        
        self.lbl_meta_name = QLabel("-")
        self.lbl_meta_name.setWordWrap(True)
        self.lbl_meta_name.setStyleSheet("font-weight: bold; border: none;")
        self.lbl_meta_size = QLabel("-")
        self.lbl_meta_size.setStyleSheet("border: none;")
        self.lbl_meta_dim = QLabel("-")
        self.lbl_meta_dim.setStyleSheet("border: none;")
        
        right_layout.addWidget(self.lbl_meta_name)
        right_layout.addWidget(self.lbl_meta_size)
        right_layout.addWidget(self.lbl_meta_dim)
        
        right_layout.addStretch()
        
        top_layout.addWidget(self.right_sidebar)
        main_layout.addLayout(top_layout, stretch=1)
        
        # --- Bottom Area (Filmstrip) ---
        bottom_layout = QVBoxLayout()
        bottom_layout.setSpacing(0)
        
        # Filters
        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(15, 5, 15, 5)
        lbl_filter = QLabel("Filter:")
        self.btn_filter_all = QPushButton("Semua")
        self.btn_filter_unassigned = QPushButton("Belum Assign")
        
        self.btn_filter_all.clicked.connect(lambda: self.set_filter("all"))
        self.btn_filter_unassigned.clicked.connect(lambda: self.set_filter("unassigned"))
        
        filter_layout.addWidget(lbl_filter)
        filter_layout.addWidget(self.btn_filter_all)
        filter_layout.addWidget(self.btn_filter_unassigned)
        filter_layout.addStretch()
        
        bottom_layout.addLayout(filter_layout)
        
        # Filmstrip
        self.filmstrip = FilmstripWidget()
        self.filmstrip.cell_clicked.connect(self.go_to_absolute_index)
        bottom_layout.addWidget(self.filmstrip)
        
        # Status Bar
        self.status_bar = QFrame()
        self.status_bar.setFixedHeight(30)
        self.status_bar.setStyleSheet(f"background-color: {COLORS['Surface2']};")
        status_layout = QHBoxLayout(self.status_bar)
        status_layout.setContentsMargins(15, 0, 15, 0)
        
        self.lbl_status_pos = QLabel("0 / 0")
        self.lbl_status_counts = QLabel("Assigned: 0 | Belum: 0 | Skip: 0")
        
        status_layout.addWidget(self.lbl_status_pos)
        status_layout.addStretch()
        status_layout.addWidget(self.lbl_status_counts)
        
        bottom_layout.addWidget(self.status_bar)
        
        main_layout.addLayout(bottom_layout)

    def load_session(self, session: SessionManager, source_folder: Path):
        self.session = session
        self.source_folder = source_folder
        self.subfolders = self.session.get_subfolders()
        self.assignments = self.session.get_all_assignments()
        self.undo_stack.clear()
        
        self.thumb_manager = ThumbnailManager(source_folder)
        
        self.setup_sidebar_buttons()
        
        # Start scanning
        self.lbl_loading.show()
        self.lbl_preview.hide()
        self.filmstrip.clear()
        
        self.scanner = FolderScanner(source_folder)
        self.scanner.files_found.connect(self.on_scan_complete)
        self.scanner.error.connect(self.on_scan_error)
        self.scanner.start()

    def setup_sidebar_buttons(self):
        # Clear old
        while self.buttons_layout.count():
            item = self.buttons_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        for i, sf in enumerate(self.subfolders):
            num = i + 1
            btn = QPushButton(f"[{num}] {sf['name']}")
            # Set background and text color to match the requested palette
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {sf['color']};
                    color: white;
                    font-weight: bold;
                    border: none;
                    text-align: left;
                    padding-left: 10px;
                }}
                QPushButton:hover {{
                    background-color: {sf['color']}dd;
                }}
            """)
            btn.setFixedHeight(40)
            # Use default argument binding to capture sf_name correctly
            btn.clicked.connect(lambda checked, name=sf['name']: self.action_assign(name))
            self.buttons_layout.addWidget(btn)
            
    def add_subfolder(self):
        name = self.input_subfolder.text().strip()
        if not name: return
        if any(sf["name"].lower() == name.lower() for sf in self.subfolders): return
        if len(self.subfolders) >= 9: return
        
        from app.settings import SUBFOLDER_COLORS
        color = SUBFOLDER_COLORS[len(self.subfolders)]
        order = len(self.subfolders) + 1
        
        self.session.upsert_subfolder(name, color, order)
        self.subfolders.append({
            "name": name,
            "color": color,
            "sort_order": order
        })
        self.setup_sidebar_buttons()
        self.input_subfolder.clear()

    def on_scan_complete(self, paths: list[Path]):
        self.paths = paths
        
        # Ensure all paths exist in assignments dict
        for p in paths:
            if str(p) not in self.assignments:
                self.assignments[str(p)] = None
                
        self.lbl_loading.hide()
        self.lbl_preview.show()
        
        self.filmstrip.populate(self.paths)
        
        # Restore badges on filmstrip
        for i, p in enumerate(self.paths):
            ass = self.assignments.get(str(p))
            if ass:
                color = self.get_color_for_subfolder(ass)
                self.filmstrip.update_cell_assignment(i, ass, color)
                
        self.set_filter("all")
        self.update_status_counts()

    def on_scan_error(self, err_msg: str):
        self.lbl_loading.setText(f"Error: {err_msg}")

    # --- Filtering & Nav ---

    def set_filter(self, mode: str):
        self.filter_mode = mode
        self.filtered_indices.clear()
        
        if mode == "all":
            self.filtered_indices = list(range(len(self.paths)))
            self.btn_filter_all.setStyleSheet(f"background-color: {COLORS['Surface2']};")
            self.btn_filter_unassigned.setStyleSheet("")
        elif mode == "unassigned":
            self.filtered_indices = [i for i, p in enumerate(self.paths) if not self.assignments.get(str(p))]
            self.btn_filter_unassigned.setStyleSheet(f"background-color: {COLORS['Surface2']};")
            self.btn_filter_all.setStyleSheet("")
            
        if self.filtered_indices:
            self.go_to_filtered_index(0)
        else:
            self.lbl_preview.clear()
            self.lbl_preview.setText("Tidak ada foto di filter ini.")
            self.lbl_status_pos.setText("0 / 0")

    def go_to_absolute_index(self, abs_idx: int):
        if abs_idx < 0 or abs_idx >= len(self.paths):
            return
            
        # If in a filter, we might need to change the filter if the user clicked the filmstrip
        # But for now, let's just go there.
        self.current_idx = abs_idx
        self.filmstrip.set_active_index(abs_idx)
        self.load_preview(abs_idx)
        self.update_status_pos()

    def go_to_filtered_index(self, filt_idx: int):
        if not self.filtered_indices:
            return
        # Clamp
        filt_idx = max(0, min(filt_idx, len(self.filtered_indices) - 1))
        abs_idx = self.filtered_indices[filt_idx]
        self.go_to_absolute_index(abs_idx)

    def next_photo(self):
        if not self.filtered_indices: return
        try:
            curr_filt = self.filtered_indices.index(self.current_idx)
            if curr_filt < len(self.filtered_indices) - 1:
                self.go_to_filtered_index(curr_filt + 1)
        except ValueError:
             # Current is not in filter, just jump to first
             self.go_to_filtered_index(0)

    def prev_photo(self):
        if not self.filtered_indices: return
        try:
            curr_filt = self.filtered_indices.index(self.current_idx)
            if curr_filt > 0:
                self.go_to_filtered_index(curr_filt - 1)
        except ValueError:
             self.go_to_filtered_index(0)

    # --- Loading & Previews ---

    def load_preview(self, abs_idx: int):
        path = self.paths[abs_idx]
        
        # Update metadata
        self.lbl_meta_name.setText(path.name)
        size_mb = os.path.getsize(str(path)) / (1024 * 1024)
        self.lbl_meta_size.setText(f"{size_mb:.2f} MB")
        self.lbl_meta_dim.setText(path.suffix.upper()[1:])
        
        # Update colored status line
        self.update_main_preview_status(abs_idx)
        
        # Pre-cache thumbnails for filmstrip sliding window
        window = THUMB_SLIDING_WINDOW // 2
        for i in range(max(0, abs_idx - window), min(len(self.paths), abs_idx + window + 1)):
            if i != abs_idx:
                self._request_thumb(i, is_main_preview=False)
                
        # Load main preview instantly if possible
        ext = path.suffix.lower()
        if ext in ['.jpg', '.jpeg', '.png', '.bmp']:
            pixmap = QPixmap(str(path))
            if not pixmap.isNull():
                self._apply_full_pixmap(pixmap)
                # Also update filmstrip since we already have the image
                self.filmstrip.update_cell_image(abs_idx, pixmap)
                return

        self._request_thumb(abs_idx, is_main_preview=True)

    def _apply_full_pixmap(self, pixmap: QPixmap):
        scaled = pixmap.scaled(
            self.preview_container.size(), 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        self.lbl_preview.setPixmap(scaled)

    def _request_thumb(self, idx: int, is_main_preview: bool):
        if not self.thumb_manager: return
        path = self.paths[idx]
        
        # Check disk cache first
        cached = self.thumb_manager.get_thumbnail_path_if_exists(path)
        if cached:
            self._apply_thumb(idx, cached, is_main_preview)
        else:
            self.thumb_manager.request_thumbnail(
                path, 
                lambda p, t: self._on_thumb_generated(idx, p, t, is_main_preview),
                priority=0 if is_main_preview else 1
            )

    def _on_thumb_generated(self, expected_idx: int, original_path: Path, thumb_path: str, is_main_preview: bool):
        # Callback from background thread
        if self.paths[expected_idx] == original_path:
             self._apply_thumb(expected_idx, thumb_path, is_main_preview)

    def _apply_thumb(self, idx: int, thumb_path: str, is_main_preview: bool):
        pixmap = QPixmap(thumb_path)
        
        # Always update filmstrip
        self.filmstrip.update_cell_image(idx, pixmap)
        
        # Update main preview if this is the currently active index
        if is_main_preview and idx == self.current_idx:
            self._apply_full_pixmap(pixmap)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Re-scale current preview on resize
        if self.current_idx >= 0 and self.lbl_preview.pixmap():
             self.load_preview(self.current_idx)

    # --- Actions ---

    def action_assign(self, subfolder_name: str):
        if self.current_idx < 0: return
        path_str = str(self.paths[self.current_idx])
        old_val = self.assignments.get(path_str)
        
        self.undo_stack.append((path_str, old_val))
        self.assignments[path_str] = subfolder_name
        self.session.save_assignment(path_str, subfolder_name)
        
        self.filmstrip.update_cell_assignment(
            self.current_idx, subfolder_name, self.get_color_for_subfolder(subfolder_name)
        )
        self.update_main_preview_status(self.current_idx)
        self.update_status_counts()
        self.next_photo()

    def action_skip(self):
        if self.current_idx < 0: return
        path_str = str(self.paths[self.current_idx])
        old_val = self.assignments.get(path_str)
        
        self.undo_stack.append((path_str, old_val))
        self.assignments[path_str] = "skip"
        self.session.save_assignment(path_str, "skip")
        
        self.filmstrip.update_cell_assignment(self.current_idx, "skip", None)
        self.update_main_preview_status(self.current_idx)
        self.update_status_counts()
        self.next_photo()

    def action_undo(self):
        if not self.undo_stack: return
        
        path_str, old_val = self.undo_stack.pop()
        
        # Find index
        try:
            abs_idx = self.paths.index(Path(path_str))
            
            self.assignments[path_str] = old_val
            self.session.save_assignment(path_str, old_val)
            
            color = self.get_color_for_subfolder(old_val) if old_val and old_val != "skip" else None
            self.filmstrip.update_cell_assignment(abs_idx, old_val, color)
            self.update_status_counts()
            
            # Update preview status line if we're currently on it
            if self.current_idx == abs_idx:
                self.update_main_preview_status(abs_idx)
            
            # Jump back to it
            self.go_to_absolute_index(abs_idx)
            
        except ValueError:
            pass

    def get_color_for_subfolder(self, name: str) -> str | None:
        for sf in self.subfolders:
            if sf["name"] == name:
                return sf["color"]
        return None
        
    def update_main_preview_status(self, abs_idx: int):
        path_str = str(self.paths[abs_idx])
        assigned_sf = self.assignments.get(path_str)
        if assigned_sf == "skip":
            self.status_line.setStyleSheet(f"QFrame {{ background-color: {COLORS['TextMuted']}; border-radius: 3px; }}")
        elif assigned_sf:
            color = self.get_color_for_subfolder(assigned_sf)
            if color:
                self.status_line.setStyleSheet(f"QFrame {{ background-color: {color}; border-radius: 3px; }}")
            else:
                self.status_line.setStyleSheet(f"QFrame {{ background-color: {COLORS['Surface2']}; border-radius: 3px; }}")
        else:
            self.status_line.setStyleSheet(f"QFrame {{ background-color: {COLORS['Border']}; border-radius: 3px; }}")

    # --- Status Updates ---

    def update_status_pos(self):
        if not self.filtered_indices:
            self.lbl_status_pos.setText("0 / 0")
            return
            
        try:
            curr_filt = self.filtered_indices.index(self.current_idx) + 1
            total = len(self.filtered_indices)
            self.lbl_status_pos.setText(f"{curr_filt} / {total} (Total file: {len(self.paths)})")
        except ValueError:
            self.lbl_status_pos.setText("? / ?")

    def update_status_counts(self):
        assigned = sum(1 for v in self.assignments.values() if v and v != "skip")
        skip = sum(1 for v in self.assignments.values() if v == "skip")
        unassigned = len(self.paths) - assigned - skip
        
        self.lbl_status_counts.setText(f"Assigned: {assigned} | Belum: {unassigned} | Skip: {skip}")

    # --- Keyboard ---

    def handle_keypress(self, event) -> bool:
        """Called by MainWindow. Returns True if handled."""
        key = event.key()
        modifiers = event.modifiers()
        
        # Undo (Z or Ctrl+Z)
        if key == Qt.Key.Key_Z:
            self.action_undo()
            return True
            
        # Skip (S)
        if key == Qt.Key.Key_S:
            self.action_skip()
            return True
            
        # Nav: Right / D
        if key == Qt.Key.Key_Right or key == Qt.Key.Key_D:
            self.next_photo()
            return True
            
        # Nav: Left / A
        if key == Qt.Key.Key_Left or key == Qt.Key.Key_A:
            self.prev_photo()
            return True
            
        # Subfolders: 1-9
        if Qt.Key.Key_1 <= key <= Qt.Key.Key_9:
            num = key - Qt.Key.Key_0
            if num <= len(self.subfolders):
                self.action_assign(self.subfolders[num - 1]["name"])
            return True
            
        return False

    # --- Apply ---

    def show_apply_dialog(self):
        dialog = ApplyDialog(self.session, self)
        dialog.exec()
        
        # After apply finishes, check which files were moved
        if hasattr(dialog, 'moved_paths') and dialog.moved_paths:
            moved_set = set(dialog.moved_paths)
            
            # Remove moved paths from self.paths
            self.paths = [p for p in self.paths if str(p) not in moved_set]
            
            # Remove from assignments
            for path_str in dialog.moved_paths:
                if path_str in self.assignments:
                    del self.assignments[path_str]
                    
            # Clear undo stack to prevent reverting to files that no longer exist
            self.undo_stack.clear()
            
            # If all files are gone, end session
            if not self.paths:
                self.session.clear_session()
                self.session_ended.emit()
            else:
                # Refresh UI
                self.filmstrip.clear()
                self.filmstrip.populate(self.paths)
                for i, p in enumerate(self.paths):
                    ass = self.assignments.get(str(p))
                    if ass:
                        color = self.get_color_for_subfolder(ass)
                        self.filmstrip.update_cell_assignment(i, ass, color)
                        
                self.set_filter("all")
                self.update_status_counts()
        else:
            # Nothing moved, or user cancelled
            pass
