"""
scanner.py — Folder scanner that runs in a background QThread.
Emits a list of photo paths without loading any pixel data.
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from core.formats import ALL_EXTENSIONS


class FolderScanner(QThread):
    """
    Scans a source folder for supported image files.
    Runs in a background thread to keep the UI responsive.

    Signals:
        progress(int): percentage complete (0-100)
        files_found(list): list of Path objects (absolute)
        error(str): error message if scan fails
    """

    progress = pyqtSignal(int)
    files_found = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, source_folder: Path, recursive: bool = False, parent=None):
        super().__init__(parent)
        self.source_folder = source_folder
        self.recursive = recursive
        self._cancelled = False

    def cancel(self):
        """Request the scan to stop early."""
        self._cancelled = True

    def run(self):
        try:
            results: list[Path] = []

            if self.recursive:
                all_items = list(self.source_folder.rglob("*"))
            else:
                all_items = list(self.source_folder.iterdir())

            total = len(all_items)
            if total == 0:
                self.files_found.emit([])
                return

            for i, item in enumerate(all_items):
                if self._cancelled:
                    break

                if item.is_file() and item.suffix.lower() in ALL_EXTENSIONS:
                    # Exclude files inside our own cache folder
                    if ".milipah_cache" not in item.parts:
                        results.append(item)

                # Emit progress every 100 items to avoid signal spam
                if i % 100 == 0:
                    self.progress.emit(int(i / total * 100))

            # Sort by filename for deterministic ordering
            results.sort(key=lambda p: p.name.lower())

            self.progress.emit(100)
            self.files_found.emit(results)

        except PermissionError as e:
            self.error.emit(f"Permission denied: {e}")
        except Exception as e:
            self.error.emit(f"Scan error: {e}")
