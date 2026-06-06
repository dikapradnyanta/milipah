"""
apply_worker.py — Background thread for executing file moves based on assignments.
"""

from __future__ import annotations

import logging
import shutil
import threading
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

class ApplyWorker(QThread):
    """
    Executes the actual file operations (moving files to subfolders).
    Runs in a background thread.
    """

    progress = pyqtSignal(int, int)  # current, total
    file_done = pyqtSignal(str)      # file_path
    error = pyqtSignal(str, str)     # file_path, reason
    finished_summary = pyqtSignal(dict) # result summary
    conflict_detected = pyqtSignal(str, str) # src_path, dest_path

    def __init__(self, source_folder: Path, assignments: dict[str, str | None], subfolders: list[dict], parent=None):
        super().__init__(parent)
        self.source_folder = source_folder
        self.assignments = assignments
        self.subfolders = subfolders
        self._cancelled = False
        
        self.conflict_event = threading.Event()
        self.current_resolution = ""
        self.global_resolution = ""

    def resolve_conflict(self, resolution: str):
        if resolution.endswith("_all"):
            self.global_resolution = resolution
        self.current_resolution = resolution
        self.conflict_event.set()

    def cancel(self):
        self._cancelled = True
        self.conflict_event.set() # Unblock if waiting

    def run(self):
        # Filter out files that are unassigned or skipped
        to_move = {path: sf for path, sf in self.assignments.items() if sf and sf != "skip"}
        total = len(to_move)
        
        summary = {
            "moved": 0,
            "moved_paths": [],
            "skipped_conflict": 0,
            "errors": 0,
            "cancelled": False
        }

        if total == 0:
            self.finished_summary.emit(summary)
            return

        # Ensure subdirectories exist
        for sf in self.subfolders:
            (self.source_folder / sf["name"]).mkdir(exist_ok=True)

        current = 0
        for src_path_str, subfolder_name in to_move.items():
            if self._cancelled:
                summary["cancelled"] = True
                break

            src_path = Path(src_path_str)
            dest_dir = self.source_folder / subfolder_name
            dest_path = dest_dir / src_path.name

            try:
                if not src_path.exists():
                    self.error.emit(src_path_str, "Source file not found")
                    summary["errors"] += 1
                    continue

                if dest_path.exists():
                    action = ""
                    if self.global_resolution:
                        action = self.global_resolution.replace("_all", "")
                    else:
                        self.conflict_event.clear()
                        self.conflict_detected.emit(src_path_str, str(dest_path))
                        # Wait for UI to respond
                        self.conflict_event.wait()
                        
                        if self._cancelled:
                            summary["cancelled"] = True
                            break
                        
                        action = self.current_resolution.replace("_all", "")

                    if action == "skip":
                        summary["skipped_conflict"] += 1
                        current += 1
                        self.progress.emit(current, total)
                        continue
                    elif action == "rename":
                        dest_path = self._generate_unique_name(dest_path)
                    elif action == "overwrite":
                        dest_path.unlink(missing_ok=True)
                    else:
                        # Cancelled from dialog or unknown action
                        continue

                # Execute the move
                shutil.move(str(src_path), str(dest_path))
                
                summary["moved"] += 1
                summary["moved_paths"].append(src_path_str)
                self.file_done.emit(src_path_str)

            except Exception as e:
                logging.error(f"Error moving {src_path_str}: {e}")
                self.error.emit(src_path_str, str(e))
                summary["errors"] += 1

            current += 1
            self.progress.emit(current, total)

        self.finished_summary.emit(summary)

    def _generate_unique_name(self, dest_path: Path) -> Path:
        """Appends _1, _2 etc to filename if it exists."""
        counter = 1
        new_path = dest_path
        while new_path.exists():
            new_path = dest_path.with_stem(f"{dest_path.stem}_{counter}")
            counter += 1
        return new_path
