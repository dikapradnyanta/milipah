"""
apply_dialog.py — Dialog shown before applying assignments.
Handles conflict resolution and shows progress during execution.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QProgressBar, QMessageBox
)

from app.settings import COLORS
from core.apply_worker import ApplyWorker


class ApplyDialog(QDialog):
    """
    Shows a summary of assignments, asks for conflict resolution preference,
    and runs the ApplyWorker.
    """

    def __init__(self, session_manager, parent=None):
        super().__init__(parent)
        self.session = session_manager
        self.setWindowTitle("Review & Apply")
        self.setFixedSize(600, 500)
        self.setModal(True)
        
        self.assignments = self.session.get_all_assignments()
        self.subfolders = self.session.get_subfolders()
        
        self.worker: ApplyWorker | None = None
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 1. Summary Table
        lbl_summary = QLabel("Ringkasan Assignment:")
        lbl_summary.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(lbl_summary)

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Folder", "Jumlah File"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setStyleSheet(f"background-color: {COLORS['Surface']}; border: 1px solid {COLORS['Border']};")
        layout.addWidget(self.table)
        
        self.populate_summary()

        # Conflict Resolution UI removed - will ask interactively if needed

        # 3. Progress Area (Hidden initially)
        self.lbl_progress = QLabel("Memindahkan file...")
        self.lbl_progress.hide()
        layout.addWidget(self.lbl_progress)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # 4. Buttons
        self.btn_layout = QHBoxLayout()
        
        self.btn_cancel = QPushButton("Batal")
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_apply = QPushButton("Apply Sekarang")
        self.btn_apply.setObjectName("ctaButton")
        self.btn_apply.clicked.connect(self.start_apply)
        
        self.btn_close = QPushButton("Tutup")
        self.btn_close.clicked.connect(self.accept)
        self.btn_close.hide()

        self.btn_layout.addStretch()
        self.btn_layout.addWidget(self.btn_cancel)
        self.btn_layout.addWidget(self.btn_apply)
        self.btn_layout.addWidget(self.btn_close)
        
        layout.addLayout(self.btn_layout)

    def populate_summary(self):
        counts = {sf["name"]: 0 for sf in self.subfolders}
        counts["[Skip]"] = 0
        counts["[Belum]"] = 0
        
        total_files = len(self.assignments)
        
        for sf in self.assignments.values():
            if sf == "skip":
                counts["[Skip]"] += 1
            elif sf is None:
                counts["[Belum]"] += 1
            elif sf in counts:
                counts[sf] += 1
                
        self.table.setRowCount(len(counts) + 1)
        
        row = 0
        for name, count in counts.items():
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(str(count)))
            row += 1
            
        # Total
        item_total = QTableWidgetItem("TOTAL")
        item_total.setFont(self.font())
        self.table.setItem(row, 0, item_total)
        self.table.setItem(row, 1, QTableWidgetItem(str(total_files)))

    def start_apply(self):
        # Lock UI
        self.btn_apply.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        self.table.setEnabled(False)
        self.table.setEnabled(False)
        
        self.lbl_progress.show()
        self.progress_bar.show()

        # Start worker
        self.worker = ApplyWorker(
            self.session.source_folder, 
            self.assignments, 
            self.subfolders
        )
        self.worker.progress.connect(self.update_progress)
        self.worker.finished_summary.connect(self.on_apply_finished)
        self.worker.conflict_detected.connect(self.on_conflict_detected)
        self.worker.start()

    def on_conflict_detected(self, src_path_str: str, dest_path_str: str):
        from pathlib import Path
        src_name = Path(src_path_str).name
        dest_dir = Path(dest_path_str).parent.name
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Konflik File")
        msg.setText(f"File '{src_name}' sudah ada di folder '{dest_dir}'.")
        msg.setInformativeText("Apa yang ingin Anda lakukan untuk file ini?")
        
        btn_skip = msg.addButton("Skip", QMessageBox.ButtonRole.ActionRole)
        btn_skip_all = msg.addButton("Skip All", QMessageBox.ButtonRole.ActionRole)
        btn_rename = msg.addButton("Rename (_1, _2)", QMessageBox.ButtonRole.ActionRole)
        btn_rename_all = msg.addButton("Rename All", QMessageBox.ButtonRole.ActionRole)
        btn_overwrite = msg.addButton("Overwrite", QMessageBox.ButtonRole.DestructiveRole)
        btn_overwrite_all = msg.addButton("Overwrite All", QMessageBox.ButtonRole.DestructiveRole)
        
        msg.exec()
        
        clicked = msg.clickedButton()
        res = "skip"
        if clicked == btn_skip_all:
            res = "skip_all"
        elif clicked == btn_rename:
            res = "rename"
        elif clicked == btn_rename_all:
            res = "rename_all"
        elif clicked == btn_overwrite:
            res = "overwrite"
        elif clicked == btn_overwrite_all:
            res = "overwrite_all"
            
        self.worker.resolve_conflict(res)

    def update_progress(self, current, total):
        pct = int(current / total * 100) if total > 0 else 100
        self.progress_bar.setValue(pct)
        self.lbl_progress.setText(f"Memindahkan file... {current} / {total}")

    def on_apply_finished(self, summary):
        self.progress_bar.setValue(100)
        
        msg = f"Selesai.\nBerhasil pindah: {summary['moved']}\n"
        if summary['skipped_conflict'] > 0:
            msg += f"Konflik dilewati: {summary['skipped_conflict']}\n"
        if summary['errors'] > 0:
            msg += f"Error: {summary['errors']}\n(Lihat log error jika ada file yang gagal)"
            
        self.lbl_progress.setText(msg)
        
        # Instead of clearing the whole session, we only remove the assignments 
        # that were successfully moved. This allows the user to continue the session.
        if summary['moved_paths']:
            self.session.remove_assignments(summary['moved_paths'])
            self.moved_paths = summary['moved_paths']
        else:
            self.moved_paths = []
        
        self.btn_cancel.hide()
        self.btn_apply.hide()
        self.btn_close.show()
        
    def closeEvent(self, event):
        # Don't allow closing with X button if worker is running
        if self.worker and self.worker.isRunning():
            event.ignore()
        else:
            event.accept()
