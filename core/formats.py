"""
formats.py — Supported file extensions for Milipah.
Single source of truth used by scanner and thumbnail generator.
"""

# Standard image formats handled by Pillow
STANDARD_EXTENSIONS: set[str] = {
    ".jpg", ".jpeg",
    ".png",
    ".webp",
    ".bmp",
    ".tif", ".tiff",
    ".gif",
}

# RAW camera formats handled by rawpy / LibRaw
RAW_EXTENSIONS: set[str] = {
    ".cr2", ".cr3",   # Canon
    ".nef", ".nrw",   # Nikon
    ".arw", ".srf",   # Sony
    ".raf",           # Fujifilm
    ".orf",           # Olympus / OM System
    ".rw2",           # Panasonic
    ".pef",           # Pentax / Ricoh
    ".dng",           # Adobe DNG / Leica / Pentax
    ".rwl",           # Leica
}

ALL_EXTENSIONS: set[str] = STANDARD_EXTENSIONS | RAW_EXTENSIONS


def is_supported(path_str: str) -> bool:
    """Return True if the file extension is supported."""
    import os
    ext = os.path.splitext(path_str)[1].lower()
    return ext in ALL_EXTENSIONS


def is_raw(path_str: str) -> bool:
    """Return True if the file is a RAW camera format."""
    import os
    ext = os.path.splitext(path_str)[1].lower()
    return ext in RAW_EXTENSIONS
