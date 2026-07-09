from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from deckflow.db.repository._helpers import dump_json, json_safe
from deckflow.local_time import local_day_start


class CollectionsMixin:
    def upsert_collection(
        self,
        slug: str,
        title: str,
        source_file: str,
        description: str | None = None,
        config: dict[str, Any] | None = None,
        meta: dict[str, Any] | None = None,
    ) -> int:
        conn = self.connect()
        conn.execute(
            """
            INSERT INTO collections (slug, title, description, config_json, meta_json, source_file)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET
                title = excluded.title,
                description = excluded.description,
                config_json = excluded.config_json,
                meta_json = excluded.meta_json,
                source_file = excluded.source_file
            """,
            (
                slug,
                title,
                description,
                json.dumps(json_safe(config or {})),
                dump_json(meta),
                source_file,
            ),
        )
        row = conn.execute("SELECT id FROM collections WHERE slug = ?", (slug,)).fetchone()
        assert row is not None
        conn.commit()
        return int(row["id"])

    def _collection_row_to_dict(self, row: Any) -> dict[str, Any]:
        return {
            "id": int(row["id"]),
            "slug": row["slug"],
            "title": row["title"],
            "description": row["description"],
            "config": json.loads(row["config_json"]),
            "meta": json.loads(row["meta_json"] or "{}"),
        }

    def list_collections(self) -> list[dict[str, Any]]:
        conn = self.connect()
        rows = conn.execute(
            """
            SELECT id, slug, title, description, config_json, meta_json
            FROM collections
            ORDER BY id
            """
        ).fetchall()
        return [self._collection_row_to_dict(row) for row in rows]

    def get_collection_id_for_deck(self, deck_id: int) -> int | None:
        conn = self.connect()
        row = conn.execute(
            "SELECT collection_id FROM decks WHERE id = ?",
            (deck_id,),
        ).fetchone()
        if row is None or row["collection_id"] is None:
            return None
        return int(row["collection_id"])

    def get_collection_id_for_card(self, card_id: int) -> int | None:
        conn = self.connect()
        row = conn.execute(
            """
            SELECT d.collection_id
            FROM cards c
            JOIN decks d ON d.id = c.deck_id
            WHERE c.id = ?
            """,
            (card_id,),
        ).fetchone()
        if row is None or row["collection_id"] is None:
            return None
        return int(row["collection_id"])

    def count_due_for_collection(
        self,
        collection_id: int,
        now: datetime | None = None,
    ) -> int:
        conn = self.connect()
        now = now or datetime.now(UTC)
        row = conn.execute(
            """
            SELECT COUNT(*) AS cnt
            FROM scheduling s
            JOIN cards c ON c.id = s.card_id
            JOIN decks d ON d.id = c.deck_id
            WHERE d.collection_id = ?
              AND s.due <= ?
              AND COALESCE(json_extract(c.meta_json, '$.status'), 'active') != 'suspended'
              AND (
                  json_extract(c.meta_json, '$.card_config.suspend') IS NULL
                  OR json_extract(c.meta_json, '$.card_config.suspend') = json('false')
              )
            """,
            (collection_id, now.isoformat()),
        ).fetchone()
        return int(row["cnt"])

    def count_total_cards_for_collection(self, collection_id: int) -> int:
        conn = self.connect()
        row = conn.execute(
            """
            SELECT COUNT(*) AS cnt
            FROM cards c
            JOIN decks d ON d.id = c.deck_id
            WHERE d.collection_id = ?
            """,
            (collection_id,),
        ).fetchone()
        return int(row["cnt"])

    def count_reviewed_today_for_collection(
        self,
        collection_id: int,
        now: datetime | None = None,
    ) -> int:
        conn = self.connect()
        start = local_day_start(now)
        row = conn.execute(
            """
            SELECT COUNT(*) AS cnt
            FROM reviews r
            JOIN cards c ON c.id = r.card_id
            JOIN decks d ON d.id = c.deck_id
            WHERE d.collection_id = ? AND r.reviewed_at >= ?
            """,
            (collection_id, start.isoformat()),
        ).fetchone()
        return int(row["cnt"])

    def get_active_collection_ids(self) -> list[int | None]:
        conn = self.connect()
        rows = conn.execute("SELECT DISTINCT collection_id FROM decks").fetchall()
        ids: list[int | None] = []
        for row in rows:
            if row["collection_id"] is None:
                ids.append(None)
            else:
                ids.append(int(row["collection_id"]))
        return ids

    def count_reviewed_today_for_orphan_decks(self, now: datetime | None = None) -> int:
        conn = self.connect()
        start = local_day_start(now)
        row = conn.execute(
            """
            SELECT COUNT(*) AS cnt
            FROM reviews r
            JOIN cards c ON c.id = r.card_id
            JOIN decks d ON d.id = c.deck_id
            WHERE d.collection_id IS NULL AND r.reviewed_at >= ?
            """,
            (start.isoformat(),),
        ).fetchone()
        return int(row["cnt"])

    def get_collection_config(self, collection_id: int | None = None) -> dict[str, Any]:
        conn = self.connect()
        if collection_id:
            row = conn.execute(
                "SELECT config_json FROM collections WHERE id = ?",
                (collection_id,),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT config_json FROM collections ORDER BY id DESC LIMIT 1"
            ).fetchone()
        if not row:
            return {}
        loaded: dict[str, Any] = json.loads(row["config_json"])
        return loaded

    def get_latest_collection(self) -> dict[str, Any] | None:
        collections = self.list_collections()
        return collections[-1] if collections else None

    def get_concept_parent_map(self) -> dict[int, int | None]:
        conn = self.connect()
        rows = conn.execute("SELECT id, parent_id FROM concepts").fetchall()
        return {int(row["id"]): row["parent_id"] for row in rows}
