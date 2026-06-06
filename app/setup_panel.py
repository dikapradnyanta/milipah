"""
setup_panel.py — Initial screen to pick folder and define subfolders.
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QLineEdit, QListWidget, QListWidgetItem, QCheckBox
)

from app.settings import SUBFOLDER_COLORS


class SetupPanel(QWidget):
    """
    Panel for phase 1: Setup.
    Allows user to select a source folder and define destination subfolders.
    """
    
    session_ready = pyqtSignal(Path, list) # source_folder, list of subfolder dicts

    def __init__(self, parent=None):
        super().__init__(parent)
        self.source_folder: Path | None = None
        self.subfolders: list[dict] = []
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Title
        title = QLabel("Milipah Setup")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)

        # 1. Source Folder Selection
        folder_layout = QHBoxLayout()
        self.btn_pick_folder = QPushButton("Select Source Folder...")
        self.btn_pick_folder.clicked.connect(self.pick_folder)
        self.lbl_folder_path = QLabel("No folder selected")
        self.lbl_folder_path.setStyleSheet("color: #888780;")
        
        folder_layout.addWidget(self.btn_pick_folder)
        folder_layout.addWidget(self.lbl_folder_path, stretch=1)
        layout.addLayout(folder_layout)

        # Recursive toggle
        self.chk_recursive = QCheckBox("Scan subfolders too (Recursive)")
        layout.addWidget(self.chk_recursive)

        # Separator
        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #2e2e2e;")
        layout.addWidget(sep)

        # 2. Subfolders
        sub_title = QLabel("Target Subfolders")
        sub_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(sub_title)

        add_sub_layout = QHBoxLayout()
        self.input_subfolder = QLineEdit()
        self.input_subfolder.setPlaceholderText("New subfolder name...")
        self.input_subfolder.returnPressed.connect(self.add_subfolder)
        
        self.btn_add_subfolder = QPushButton("Add")
        self.btn_add_subfolder.clicked.connect(self.add_subfolder)
        
        add_sub_layout.addWidget(self.input_subfolder)
        add_sub_layout.addWidget(self.btn_add_subfolder)
        layout.addLayout(add_sub_layout)

        self.list_subfolders = QListWidget()
        self.list_subfolders.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        layout.addWidget(self.list_subfolders)
        
        self.btn_remove_subfolder = QPushButton("Remove Selected Subfolder")
        self.btn_remove_subfolder.clicked.connect(self.remove_subfolder)
        self.btn_remove_subfolder.setEnabled(False)
        self.list_subfolders.itemSelectionChanged.connect(
            lambda: self.btn_remove_subfolder.setEnabled(bool(self.list_subfolders.selectedItems()))
        )
        layout.addWidget(self.btn_remove_subfolder)

        layout.addStretch()

        # 3. Start CTA
        self.btn_start = QPushButton("Start Sorting")
        self.btn_start.setObjectName("ctaButton")
        self.btn_start.setFixedHeight(50)
        self.btn_start.setEnabled(False)
        self.btn_start.clicked.connect(self.start)
        layout.addWidget(self.btn_start)

    def pick_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Source Folder")
        if folder:
            self.source_folder = Path(folder)
            self.lbl_folder_path.setText(str(self.source_folder))
            
            # Auto-detect existing subdirectories
            try:
                for entry in self.source_folder.iterdir():
                    if entry.is_dir() and not entry.name.startswith('.'):
                        if len(self.subfolders) >= 9:
                            break
                        # Prevent duplicates
                        if not any(sf["name"].lower() == entry.name.lower() for sf in self.subfolders):
                            color = SUBFOLDER_COLORS[len(self.subfolders)]
                            order = len(self.subfolders) + 1
                            self.subfolders.append({
                                "name": entry.name,
                                "color": color,
                                "sort_order": order
                            })
                self.update_subfolder_list()
            except Exception:
                pass
                
            self.check_ready()

    def add_subfolder(self):
        name = self.input_subfolder.text().strip()
        if not name:
            return
            
        # Prevent duplicates
        if any(sf["name"].lower() == name.lower() for sf in self.subfolders):
            return
            
        # Max 9 subfolders for keyboard shortcuts
        if len(self.subfolders) >= 9:
            return

        color = SUBFOLDER_COLORS[len(self.subfolders)]
        order = len(self.subfolders) + 1
        
        self.subfolders.append({
            "name": name,
            "color": color,
            "sort_order": order
        })
        
        self.update_subfolder_list()
        self.input_subfolder.clear()
        self.check_ready()

    def remove_subfolder(self):
        selected = self.list_subfolders.selectedItems()
        if not selected:
            return
            
        row = self.list_subfolders.row(selected[0])
        self.subfolders.pop(row)
        
        # Reassign colors and order
        for i, sf in enumerate(self.subfolders):
            sf["color"] = SUBFOLDER_COLORS[i]
            sf["sort_order"] = i + 1
            
        self.update_subfolder_list()
        self.check_ready()

    def update_subfolder_list(self):
        self.list_subfolders.clear()
        for i, sf in enumerate(self.subfolders):
            # Show the keyboard shortcut (1-9) in the item text
            item = QListWidgetItem(f"[{i+1}]  {sf['name']}")
            # Set text color to match the assigned button color
            item.setForeground(Qt.GlobalColor.white) 
            self.list_subfolders.addItem(item)

    def check_ready(self):
        is_ready = self.source_folder is not None and len(self.subfolders) > 0
        self.btn_start.setEnabled(is_ready)

    def start(self):
        if self.source_folder and self.subfolders:
            self.session_ready.emit(self.source_folder, self.subfolders)

    def reset(self):
        self.source_folder = None
        self.lbl_folder_path.setText("No folder selected")
        self.subfolders.clear()
        self.update_subfolder_list()
        self.check_ready()
