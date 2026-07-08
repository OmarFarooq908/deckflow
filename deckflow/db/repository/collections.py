from __future__ import annotations

import json
from typing import Any

from deckflow.db.repository._helpers import dump_json, json_safe


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
        conn = self.connect()
        row = conn.execute(
            """
            SELECT id, slug, title, description, config_json, meta_json
            FROM collections ORDER BY id DESC LIMIT 1
            """
        ).fetchone()
        if not row:
            return None
        return {
            "id": int(row["id"]),
            "slug": row["slug"],
            "title": row["title"],
            "description": row["description"],
            "config": json.loads(row["config_json"]),
            "meta": json.loads(row["meta_json"] or "{}"),
        }

    def get_concept_parent_map(self) -> dict[int, int | None]:
        conn = self.connect()
        rows = conn.execute("SELECT id, parent_id FROM concepts").fetchall()
        return {int(row["id"]): row["parent_id"] for row in rows}
