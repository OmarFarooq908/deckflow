from __future__ import annotations

import sqlite3
from pathlib import Path

from deckflow.db.schema import SCHEMA_SQL


class BaseRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._conn: sqlite3.Connection | None = None
        self._active_session_id: int | None = None

    def connect(self) -> sqlite3.Connection:
        if self._conn is None:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON")
        return self._conn

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def reset_active_session(self) -> None:
        self._active_session_id = None

    def initialize(self) -> None:
        conn = self.connect()
        has_cards = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'cards'"
        ).fetchone()
        if not has_cards:
            conn.executescript(SCHEMA_SQL)
        self._migrate(conn)
        conn.commit()

    def _migrate(self, conn: sqlite3.Connection) -> None:
        deck_cols = {row[1] for row in conn.execute("PRAGMA table_info(decks)")}
        card_cols = {row[1] for row in conn.execute("PRAGMA table_info(cards)")}
        review_cols = {row[1] for row in conn.execute("PRAGMA table_info(reviews)")}

        if "meta_json" not in deck_cols:
            conn.execute("ALTER TABLE decks ADD COLUMN meta_json TEXT NOT NULL DEFAULT '{}'")
        if "collection_id" not in deck_cols:
            conn.execute("ALTER TABLE decks ADD COLUMN collection_id INTEGER")
        if "card_uid" not in card_cols:
            conn.execute("ALTER TABLE cards ADD COLUMN card_uid TEXT")
        if "meta_json" not in card_cols:
            conn.execute("ALTER TABLE cards ADD COLUMN meta_json TEXT NOT NULL DEFAULT '{}'")

        for col, typedef in [
            ("session_id", "INTEGER"),
            ("reveal_ms", "INTEGER"),
            ("rating_ms", "INTEGER"),
            ("retrievability", "REAL"),
            ("stability", "REAL"),
            ("difficulty", "REAL"),
            ("state", "INTEGER"),
            ("fsrs_snapshot_json", "TEXT"),
        ]:
            if col not in review_cols:
                conn.execute(f"ALTER TABLE reviews ADD COLUMN {col} {typedef}")

        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_cards_deck_uid ON cards(deck_id, card_uid)"
        )
