from __future__ import annotations

import sqlite3
from pathlib import Path


class PostStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS posted_news (
                    id TEXT PRIMARY KEY,
                    posted_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def already_posted(self, item_id: str) -> bool:
        with self._connect() as conn:
            row = conn.execute("SELECT 1 FROM posted_news WHERE id = ?", (item_id,)).fetchone()
            return row is not None

    def mark_posted(self, item_id: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO posted_news(id, posted_at) VALUES (?, datetime('now'))",
                (item_id,),
            )
            conn.commit()
