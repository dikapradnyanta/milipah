"""
session.py — SQLite-based session persistence for Milipah.
Stores assignments and subfolder configuration so sessions survive app restarts.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional


CACHE_DIR_NAME = ".milipah_cache"
DB_NAME = "session.db"


class SessionManager:
    """
    Manages the SQLite session database stored inside the source folder's
    .milipah_cache directory.

    The database tracks:
      - session metadata (source folder, timestamps)
      - photo assignments (file path → subfolder or None or 'skip')
      - subfolder definitions (name, color, order)
    """

    def __init__(self, source_folder: Path):
        self.source_folder = source_folder
        self.cache_dir = source_folder / CACHE_DIR_NAME
        self.db_path = self.cache_dir / DB_NAME
        self._conn: Optional[sqlite3.Connection] = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def open(self):
        """Create cache dir and open (or create) the database."""
        self.cache_dir.mkdir(exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def _create_tables(self):
        assert self._conn
        cur = self._conn.cursor()
        cur.executescript("""
            PRAGMA journal_mode=WAL;

            CREATE TABLE IF NOT EXISTS session (
                id          INTEGER PRIMARY KEY,
                folder_src  TEXT NOT NULL,
                created_at  TEXT,
                updated_at  TEXT
            );

            CREATE TABLE IF NOT EXISTS assignments (
                file_path   TEXT PRIMARY KEY,
                subfolder   TEXT,
                updated_at  TEXT
            );

            CREATE TABLE IF NOT EXISTS subfolders (
                name        TEXT PRIMARY KEY,
                color       TEXT,
                sort_order  INTEGER
            );
        """)
        self._conn.commit()

    # ------------------------------------------------------------------
    # Session record
    # ------------------------------------------------------------------

    def init_session(self):
        """Insert or refresh the session record for this source folder."""
        assert self._conn
        now = datetime.now().isoformat()
        cur = self._conn.cursor()
        cur.execute("SELECT id FROM session WHERE folder_src = ?",
                    (str(self.source_folder),))
        row = cur.fetchone()
        if row:
            cur.execute("UPDATE session SET updated_at = ? WHERE folder_src = ?",
                        (now, str(self.source_folder)))
        else:
            cur.execute(
                "INSERT INTO session (folder_src, created_at, updated_at) VALUES (?, ?, ?)",
                (str(self.source_folder), now, now),
            )
        self._conn.commit()

    def clear_session(self):
        """Wipe all assignments and subfolders (fresh start)."""
        assert self._conn
        cur = self._conn.cursor()
        cur.execute("DELETE FROM assignments")
        cur.execute("DELETE FROM subfolders")
        cur.execute("DELETE FROM session")
        self._conn.commit()

    # ------------------------------------------------------------------
    # Subfolders
    # ------------------------------------------------------------------

    def save_subfolders(self, subfolders: list[dict]):
        """
        Persist subfolder list.
        Each dict: {'name': str, 'color': str, 'sort_order': int}
        """
        assert self._conn
        cur = self._conn.cursor()
        cur.execute("DELETE FROM subfolders")
        cur.executemany(
            "INSERT INTO subfolders (name, color, sort_order) VALUES (:name, :color, :sort_order)",
            subfolders,
        )
        self._conn.commit()

    def get_subfolders(self) -> list[dict]:
        """Return saved subfolders ordered by sort_order."""
        assert self._conn
        cur = self._conn.cursor()
        cur.execute("SELECT name, color, sort_order FROM subfolders ORDER BY sort_order")
        return [dict(row) for row in cur.fetchall()]

    def upsert_subfolder(self, name: str, color: str, sort_order: int):
        """Insert or update a single subfolder."""
        assert self._conn
        cur = self._conn.cursor()
        cur.execute(
            "INSERT INTO subfolders (name, color, sort_order) VALUES (?, ?, ?) "
            "ON CONFLICT(name) DO UPDATE SET color=excluded.color, sort_order=excluded.sort_order",
            (name, color, sort_order),
        )
        self._conn.commit()

    def delete_subfolder(self, name: str):
        """Remove a subfolder definition (only call if no photos assigned)."""
        assert self._conn
        cur = self._conn.cursor()
        cur.execute("DELETE FROM subfolders WHERE name = ?", (name,))
        self._conn.commit()

    # ------------------------------------------------------------------
    # Assignments
    # ------------------------------------------------------------------

    def save_assignment(self, file_path: str, subfolder: Optional[str]):
        """
        Persist an assignment.
        subfolder=None means 'unassigned', subfolder='skip' means skipped.
        """
        assert self._conn
        now = datetime.now().isoformat()
        cur = self._conn.cursor()
        cur.execute(
            "INSERT INTO assignments (file_path, subfolder, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(file_path) DO UPDATE SET subfolder=excluded.subfolder, updated_at=excluded.updated_at",
            (file_path, subfolder, now),
        )
        self._conn.commit()

    def bulk_save_assignments(self, assignments: dict[str, Optional[str]]):
        """Persist many assignments at once (used on resume)."""
        assert self._conn
        now = datetime.now().isoformat()
        cur = self._conn.cursor()
        cur.executemany(
            "INSERT INTO assignments (file_path, subfolder, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(file_path) DO UPDATE SET subfolder=excluded.subfolder, updated_at=excluded.updated_at",
            [(fp, sf, now) for fp, sf in assignments.items()],
        )
        self._conn.commit()

    def get_all_assignments(self) -> dict[str, Optional[str]]:
        """Return {file_path: subfolder_or_None} for all recorded files."""
        assert self._conn
        cur = self._conn.cursor()
        cur.execute("SELECT file_path, subfolder FROM assignments")
        return {row["file_path"]: row["subfolder"] for row in cur.fetchall()}

    def remove_assignments(self, file_paths: list[str]):
        """Remove assignments for the given paths (used after applying)."""
        assert self._conn
        cur = self._conn.cursor()
        cur.executemany("DELETE FROM assignments WHERE file_path = ?", [(p,) for p in file_paths])
        self._conn.commit()

    # ------------------------------------------------------------------
    # Detection
    # ------------------------------------------------------------------

    @staticmethod
    def detect_existing_session(source_folder: Path) -> bool:
        """
        Return True if a session database already exists for this folder
        and it has at least one assignment record.
        """
        db_path = source_folder / CACHE_DIR_NAME / DB_NAME
        if not db_path.exists():
            return False
        try:
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM assignments")
            count = cur.fetchone()[0]
            conn.close()
            return count > 0
        except Exception:
            return False
