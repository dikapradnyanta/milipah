"""
thumbnail.py — Background thumbnail generation and caching.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps
import rawpy
from PyQt6.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal

from core.formats import is_raw

MAX_THUMBNAIL_SIZE = 800


class WorkerSignals(QObject):
    """Signals for the thumbnail worker."""
    result = pyqtSignal(Path, str)  # original_path, cached_thumb_path
    error = pyqtSignal(Path, str)   # original_path, error_message


class ThumbnailWorker(QRunnable):
    """
    Worker task to generate a thumbnail for a single image.
    Saves the thumbnail as a JPEG to the cache directory.
    """

    def __init__(self, file_path: Path, cache_dir: Path):
        super().__init__()
        self.file_path = file_path
        self.cache_dir = cache_dir
        self.signals = WorkerSignals()
        
        # Unique cache filename based on original name to avoid collisions
        self.thumb_path = self.cache_dir / f"{self.file_path.name}.thumb.jpg"

    def run(self):
        # 1. Check if cache already exists
        if self.thumb_path.exists():
            self.signals.result.emit(self.file_path, str(self.thumb_path))
            return

        try:
            # 2. Generate thumbnail
            if is_raw(str(self.file_path)):
                self._generate_raw_thumb()
            else:
                self._generate_std_thumb()

            self.signals.result.emit(self.file_path, str(self.thumb_path))
            
        except Exception as e:
            logging.error(f"Thumbnail error for {self.file_path}: {e}")
            self.signals.error.emit(self.file_path, str(e))

    def _generate_raw_thumb(self):
        """Extract or render thumbnail from RAW using rawpy."""
        with rawpy.imread(str(self.file_path)) as raw:
            try:
                # Try to extract embedded thumbnail first (much faster)
                thumb = raw.extract_thumb()
                if thumb.format in [rawpy.ThumbFormat.JPEG, rawpy.ThumbFormat.BITMAP]:
                    # Some cameras embed bitmap thumbnails, but Pillow can usually handle the bytes
                    img = Image.open(thumb.data)
                else:
                     raise ValueError(f"Unsupported thumb format: {thumb.format}")
            except (rawpy.LibRawNoThumbnailError, rawpy.LibRawUnsupportedThumbnailError, ValueError):
                # Fallback: Half-size decode (faster than full decode)
                rgb = raw.postprocess(half_size=True, use_camera_wb=True)
                img = Image.fromarray(rgb)

        img = ImageOps.exif_transpose(img) # Handle orientation
        img.thumbnail((MAX_THUMBNAIL_SIZE, MAX_THUMBNAIL_SIZE), Image.Resampling.LANCZOS)
        img.convert('RGB').save(self.thumb_path, "JPEG", quality=85)

    def _generate_std_thumb(self):
        """Generate thumbnail for standard image formats using Pillow."""
        with Image.open(self.file_path) as img:
            img = ImageOps.exif_transpose(img) # Handle orientation
            img.thumbnail((MAX_THUMBNAIL_SIZE, MAX_THUMBNAIL_SIZE), Image.Resampling.LANCZOS)
            # Ensure it's RGB for JPEG save (drops alpha from PNG/WebP)
            img.convert('RGB').save(self.thumb_path, "JPEG", quality=85)


class ThumbnailManager:
    """
    Manages background generation of thumbnails.
    """
    def __init__(self, source_folder: Path):
        self.source_folder = source_folder
        self.cache_dir = source_folder / ".milipah_cache" / "thumbnails"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.thread_pool = QThreadPool.globalInstance()
        # Leave one thread for the UI, cap at 4 for reasonable disk/CPU usage
        self.max_threads = max(1, min(4, self.thread_pool.maxThreadCount() - 1))
        self.thread_pool.setMaxThreadCount(self.max_threads)
        
        self._queued_files: set[Path] = set()

    def request_thumbnail(self, file_path: Path, result_callback, priority: int = 0):
        """
        Queue a thumbnail generation task.
        Priority: 0 is highest (current/next few photos), higher numbers are lower priority.
        QThreadPool doesn't have native dynamic priority queues in Python/PyQt6 easily accessible,
        so we just submit them. In a real highly-optimized app we'd build a custom priority queue.
        For v1, we rely on the caller to request the ±5 window first.
        """
        if file_path in self._queued_files:
            return # Already queued

        worker = ThumbnailWorker(file_path, self.cache_dir)
        worker.signals.result.connect(lambda p, t: self._on_result(p, t, result_callback))
        worker.signals.error.connect(lambda p, e: self._on_error(p))
        
        self._queued_files.add(file_path)
        self.thread_pool.start(worker)

    def _on_result(self, original_path: Path, thumb_path: str, callback):
        self._queued_files.discard(original_path)
        callback(original_path, thumb_path)
        
    def _on_error(self, original_path: Path):
        self._queued_files.discard(original_path)

    def get_thumbnail_path_if_exists(self, file_path: Path) -> str | None:
        """Returns the path to the cached thumbnail if it already exists on disk."""
        thumb_path = self.cache_dir / f"{file_path.name}.thumb.jpg"
        return str(thumb_path) if thumb_path.exists() else None
