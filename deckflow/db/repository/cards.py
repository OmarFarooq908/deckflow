from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from deckflow.db.repository._helpers import card_meta, dump_json, row_to_card
from deckflow.local_time import local_day_start
from deckflow.models.domain import CardRow, ParsedCard, SchedulingRow


class CardsMixin:
    def upsert_deck(
        self,
        path: str,
        source_file: str,
        meta: dict[str, Any] | None = None,
        collection_id: int | None = None,
    ) -> int:
        conn = self.connect()
        meta_json = dump_json(meta)
        conn.execute(
            """
            INSERT INTO decks (path, source_file, meta_json, collection_id)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(path, source_file) DO UPDATE SET
                path = excluded.path,
                meta_json = excluded.meta_json,
                collection_id = excluded.collection_id
            """,
            (path, source_file, meta_json, collection_id),
        )
        row = conn.execute(
            "SELECT id FROM decks WHERE path = ? AND source_file = ?",
            (path, source_file),
        ).fetchone()
        assert row is not None
        conn.commit()
        return int(row["id"])

    def upsert_card(self, deck_id: int, card: ParsedCard) -> int:
        conn = self.connect()
        tags_json = json.dumps(card.tags)
        meta_json = dump_json(card_meta(card))

        existing_id: int | None = None
        if card.card_uid:
            row = conn.execute(
                "SELECT id FROM cards WHERE deck_id = ? AND card_uid = ?",
                (deck_id, card.card_uid),
            ).fetchone()
            if row:
                existing_id = int(row["id"])

        if existing_id is not None:
            conn.execute(
                """
                UPDATE cards SET
                    front_md = ?, back_md = ?, card_type = ?, tags_json = ?,
                    source_line = ?, card_index = ?, meta_json = ?
                WHERE id = ?
                """,
                (
                    card.front_md,
                    card.back_md,
                    card.card_type,
                    tags_json,
                    card.source_line,
                    card.card_index,
                    meta_json,
                    existing_id,
                ),
            )
            card_id = existing_id
        else:
            conn.execute(
                """
                INSERT INTO cards (
                    deck_id, front_md, back_md, card_type, tags_json,
                    source_line, card_index, card_uid, meta_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(deck_id, card_index) DO UPDATE SET
                    front_md = excluded.front_md,
                    back_md = excluded.back_md,
                    card_type = excluded.card_type,
                    tags_json = excluded.tags_json,
                    source_line = excluded.source_line,
                    card_uid = excluded.card_uid,
                    meta_json = excluded.meta_json
                """,
                (
                    deck_id,
                    card.front_md,
                    card.back_md,
                    card.card_type,
                    tags_json,
                    card.source_line,
                    card.card_index,
                    card.card_uid,
                    meta_json,
                ),
            )
            if card.card_uid:
                row = conn.execute(
                    "SELECT id FROM cards WHERE deck_id = ? AND card_uid = ?",
                    (deck_id, card.card_uid),
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT id FROM cards WHERE deck_id = ? AND card_index = ?",
                    (deck_id, card.card_index),
                ).fetchone()
            assert row is not None
            card_id = int(row["id"])

        existing = conn.execute(
            "SELECT card_id FROM scheduling WHERE card_id = ?", (card_id,)
        ).fetchone()
        if existing is None:
            from deckflow.scheduler.fsrs import card_to_json, new_fsrs_card

            fsrs_card = new_fsrs_card(card_id)
            conn.execute(
                """
                INSERT INTO scheduling (card_id, due, fsrs_json, reps, lapses)
                VALUES (?, ?, ?, 0, 0)
                """,
                (card_id, fsrs_card.due.isoformat(), card_to_json(fsrs_card)),
            )

        if card.concepts:
            self.link_card_concepts(card_id, list(card.concepts), weight=1.0)
        else:
            self.link_card_concepts(card_id, list(card.tags), weight=0.5)
        conn.commit()
        return card_id

    def delete_cards_not_in(self, deck_id: int, keep_card_ids: set[int]) -> int:
        conn = self.connect()
        rows = conn.execute("SELECT id FROM cards WHERE deck_id = ?", (deck_id,)).fetchall()
        removed = 0
        for row in rows:
            card_id = int(row["id"])
            if card_id not in keep_card_ids:
                conn.execute("DELETE FROM cards WHERE id = ?", (card_id,))
                removed += 1
        conn.commit()
        return removed

    def prune_decks_not_in(self, source_file: str, keep_deck_ids: set[int]) -> int:
        conn = self.connect()
        rows = conn.execute(
            "SELECT id FROM decks WHERE source_file = ?",
            (source_file,),
        ).fetchall()
        removed = 0
        for row in rows:
            deck_id = int(row["id"])
            if deck_id not in keep_deck_ids:
                conn.execute("DELETE FROM decks WHERE id = ?", (deck_id,))
                removed += 1
        conn.commit()
        return removed

    def get_due_cards(self, limit: int, now: datetime | None = None) -> list[CardRow]:
        candidates = self.get_due_candidates(now=now)
        return candidates[:limit]

    def get_due_candidates(self, now: datetime | None = None) -> list[CardRow]:
        return self.get_due_candidates_filtered(now=now)

    def get_due_candidates_filtered(
        self,
        now: datetime | None = None,
        deck_prefix: str | None = None,
        concept_slug: str | None = None,
    ) -> list[CardRow]:
        conn = self.connect()
        now = now or datetime.now(UTC)
        query = """
            SELECT DISTINCT
                c.id, c.deck_id, c.front_md, c.back_md, c.card_type,
                c.tags_json, c.source_line, c.card_index, c.card_uid,
                c.meta_json, d.path AS deck_path
            FROM cards c
            JOIN scheduling s ON s.card_id = c.id
            JOIN decks d ON d.id = c.deck_id
        """
        joins: list[str] = []
        conditions = [
            "s.due <= ?",
            "COALESCE(json_extract(c.meta_json, '$.status'), 'active') != 'suspended'",
        ]
        params: list[Any] = [now.isoformat()]

        if concept_slug:
            joins.append("JOIN card_concepts cc ON cc.card_id = c.id")
            joins.append("JOIN concepts co ON co.id = cc.concept_id")
            conditions.append("(co.slug = ? OR co.slug LIKE ?)")
            params.extend([concept_slug, f"{concept_slug}::%"])

        if deck_prefix:
            pattern = self._deck_match_pattern(deck_prefix)
            conditions.append("d.path LIKE ?")
            params.append(pattern)

        if joins:
            query += " " + " ".join(joins)
        query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY s.due ASC"

        rows = conn.execute(query, params).fetchall()
        return [row_to_card(row) for row in rows]

    @staticmethod
    def _deck_match_pattern(deck_prefix: str) -> str:
        if deck_prefix.endswith("::*"):
            base = deck_prefix[:-3]
            return f"{base}%"
        return f"{deck_prefix}%"

    def get_deck_stats_by_prefix(self, prefix: str, now: datetime | None = None) -> tuple[int, int]:
        conn = self.connect()
        now = now or datetime.now(UTC)
        pattern = self._deck_match_pattern(prefix)
        row = conn.execute(
            """
            SELECT
                COUNT(c.id) AS card_count,
                SUM(CASE WHEN s.due <= ? THEN 1 ELSE 0 END) AS due_count
            FROM cards c
            JOIN decks d ON d.id = c.deck_id
            LEFT JOIN scheduling s ON s.card_id = c.id
            WHERE d.path LIKE ?
              AND COALESCE(json_extract(c.meta_json, '$.status'), 'active') != 'suspended'
            """,
            (now.isoformat(), pattern),
        ).fetchone()
        return int(row["due_count"] or 0), int(row["card_count"] or 0)

    def get_card_objective(self, card_id: int) -> str | None:
        conn = self.connect()
        row = conn.execute("SELECT meta_json FROM cards WHERE id = ?", (card_id,)).fetchone()
        if not row:
            return None
        meta = json.loads(row["meta_json"] or "{}")
        objective = meta.get("objective")
        return str(objective) if objective else None

    def get_card(self, card_id: int) -> CardRow | None:
        conn = self.connect()
        row = conn.execute(
            """
            SELECT
                c.id, c.deck_id, c.front_md, c.back_md, c.card_type,
                c.tags_json, c.source_line, c.card_index, c.card_uid,
                c.meta_json, d.path AS deck_path
            FROM cards c
            JOIN decks d ON d.id = c.deck_id
            WHERE c.id = ?
            """,
            (card_id,),
        ).fetchone()
        return row_to_card(row) if row else None

    def get_scheduling(self, card_id: int) -> SchedulingRow | None:
        conn = self.connect()
        row = conn.execute(
            "SELECT card_id, due, fsrs_json, reps, lapses FROM scheduling WHERE card_id = ?",
            (card_id,),
        ).fetchone()
        if row is None:
            return None
        return SchedulingRow(
            card_id=int(row["card_id"]),
            due=datetime.fromisoformat(row["due"]),
            fsrs_json=row["fsrs_json"],
            reps=int(row["reps"]),
            lapses=int(row["lapses"]),
        )

    def update_scheduling(
        self,
        card_id: int,
        due: datetime,
        fsrs_json: str,
        reps: int,
        lapses: int,
    ) -> None:
        conn = self.connect()
        conn.execute(
            """
            UPDATE scheduling SET due = ?, fsrs_json = ?, reps = ?, lapses = ?
            WHERE card_id = ?
            """,
            (due.isoformat(), fsrs_json, reps, lapses, card_id),
        )
        conn.commit()

    def get_card_concept_slugs(self, card_id: int) -> list[str]:
        conn = self.connect()
        rows = conn.execute(
            """
            SELECT c.slug FROM concepts c
            JOIN card_concepts cc ON cc.concept_id = c.id
            WHERE cc.card_id = ?
            ORDER BY cc.weight DESC
            """,
            (card_id,),
        ).fetchall()
        return [row["slug"] for row in rows]

    def get_weakness_for_card(self, card_id: int) -> float:
        conn = self.connect()
        row = conn.execute(
            """
            SELECT MAX(cm.weakness_score) AS weakness
            FROM card_concepts cc
            JOIN concept_mastery cm ON cm.concept_id = cc.concept_id
            WHERE cc.card_id = ?
            """,
            (card_id,),
        ).fetchone()
        return float(row["weakness"] or 0) if row else 0.0

    def count_new_cards_today(self, now: datetime | None = None) -> int:
        conn = self.connect()
        start = local_day_start(now)
        row = conn.execute(
            """
            SELECT COUNT(*) AS cnt FROM reviews r
            JOIN scheduling s ON s.card_id = r.card_id
            WHERE s.reps = 1 AND r.reviewed_at >= ?
            """,
            (start.isoformat(),),
        ).fetchone()
        return int(row["cnt"])

    def count_cards_for_concept(self, concept_slug: str, due_only: bool = False) -> int:
        conn = self.connect()
        now = datetime.now(UTC)
        due_clause = "AND s.due <= ?" if due_only else ""
        params: list[Any] = [concept_slug, f"{concept_slug}::%"]
        if due_only:
            params.append(now.isoformat())
        row = conn.execute(
            f"""
            SELECT COUNT(DISTINCT c.id) AS cnt
            FROM cards c
            JOIN card_concepts cc ON cc.card_id = c.id
            JOIN concepts co ON co.id = cc.concept_id
            LEFT JOIN scheduling s ON s.card_id = c.id
            WHERE (co.slug = ? OR co.slug LIKE ?)
              AND COALESCE(json_extract(c.meta_json, '$.status'), 'active') != 'suspended'
              {due_clause}
            """,
            params,
        ).fetchone()
        return int(row["cnt"])
