from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from deckflow.db.schema import SCHEMA_SQL
from deckflow.models.domain import (
    CardRow,
    ConceptMastery,
    DeckSummary,
    ParsedCard,
    SchedulingRow,
)


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _dump_json(data: dict[str, Any] | None) -> str:
    return json.dumps(_json_safe(data or {}))


class Repository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._conn: sqlite3.Connection | None = None
        self._active_session_id: int | None = None

    def connect(self) -> sqlite3.Connection:
        if self._conn is None:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON")
        return self._conn

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def initialize(self) -> None:
        conn = self.connect()
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

    # --- Collections ---

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
                json.dumps(_json_safe(config or {})),
                _dump_json(meta),
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

    # --- Concepts ---

    def upsert_concept(self, slug: str, label: str | None = None) -> int:
        conn = self.connect()
        label = label or slug.replace("::", " / ").replace("-", " ").title()
        parent_id = None
        if "::" in slug:
            parent_slug = slug.rsplit("::", 1)[0]
            parent_row = conn.execute(
                "SELECT id FROM concepts WHERE slug = ?", (parent_slug,)
            ).fetchone()
            parent_id = int(parent_row["id"]) if parent_row else self.upsert_concept(parent_slug)

        conn.execute(
            """
            INSERT INTO concepts (slug, label, parent_id)
            VALUES (?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET label = excluded.label
            """,
            (slug, label, parent_id),
        )
        row = conn.execute("SELECT id FROM concepts WHERE slug = ?", (slug,)).fetchone()
        assert row is not None
        conn.commit()
        return int(row["id"])

    def link_card_concepts(
        self,
        card_id: int,
        concept_slugs: list[str],
        weight: float = 1.0,
    ) -> None:
        conn = self.connect()
        for slug in concept_slugs:
            concept_id = self.upsert_concept(slug)
            conn.execute(
                """
                INSERT INTO card_concepts (card_id, concept_id, weight)
                VALUES (?, ?, ?)
                ON CONFLICT(card_id, concept_id) DO UPDATE SET weight = excluded.weight
                """,
                (card_id, concept_id, weight),
            )
        conn.commit()

    def link_card_tags_as_concepts(self, card_id: int, tags: list[str]) -> None:
        if tags:
            self.link_card_concepts(card_id, tags, weight=0.5)

    # --- Decks & cards ---

    def upsert_deck(
        self,
        path: str,
        source_file: str,
        meta: dict[str, Any] | None = None,
        collection_id: int | None = None,
    ) -> int:
        conn = self.connect()
        meta_json = _dump_json(meta)
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
        meta_json = _dump_json(self._card_meta(card))

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

        concept_slugs = list(card.concepts) if card.concepts else list(card.tags)
        if concept_slugs:
            self.link_card_concepts(card_id, concept_slugs, weight=1.0)
        conn.commit()
        return card_id

    # --- Sessions ---

    def get_or_create_session(self, collection_id: int | None = None) -> int:
        if self._active_session_id is not None:
            return self._active_session_id
        conn = self.connect()
        now = datetime.now(UTC).isoformat()
        cursor = conn.execute(
            """
            INSERT INTO review_sessions (started_at, collection_id)
            VALUES (?, ?)
            """,
            (now, collection_id),
        )
        conn.commit()
        lastrowid = cursor.lastrowid
        assert lastrowid is not None
        self._active_session_id = int(lastrowid)
        return self._active_session_id

    def increment_session(self, session_id: int) -> None:
        conn = self.connect()
        conn.execute(
            """
            UPDATE review_sessions
            SET cards_reviewed = cards_reviewed + 1
            WHERE id = ?
            """,
            (session_id,),
        )
        conn.commit()

    # --- Reviews ---

    def record_review(
        self,
        card_id: int,
        rating: int,
        reviewed_at: datetime,
        elapsed_ms: int | None = None,
        reveal_ms: int | None = None,
        rating_ms: int | None = None,
        retrievability: float | None = None,
        stability: float | None = None,
        difficulty: float | None = None,
        state: int | None = None,
        fsrs_snapshot_json: str | None = None,
        session_id: int | None = None,
    ) -> int:
        conn = self.connect()
        cursor = conn.execute(
            """
            INSERT INTO reviews (
                card_id, session_id, rating, reviewed_at, elapsed_ms,
                reveal_ms, rating_ms, retrievability, stability, difficulty,
                state, fsrs_snapshot_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                card_id,
                session_id,
                rating,
                reviewed_at.isoformat(),
                elapsed_ms,
                reveal_ms,
                rating_ms,
                retrievability,
                stability,
                difficulty,
                state,
                fsrs_snapshot_json,
            ),
        )
        if session_id:
            self.increment_session(session_id)
        conn.commit()
        lastrowid = cursor.lastrowid
        assert lastrowid is not None
        return int(lastrowid)

    # --- Card queries ---

    def get_due_cards(self, limit: int, now: datetime | None = None) -> list[CardRow]:
        candidates = self.get_due_candidates(now=now)
        return candidates[:limit]

    def get_due_candidates(self, now: datetime | None = None) -> list[CardRow]:
        conn = self.connect()
        now = now or datetime.now(UTC)
        rows = conn.execute(
            """
            SELECT
                c.id, c.deck_id, c.front_md, c.back_md, c.card_type,
                c.tags_json, c.source_line, c.card_index, c.card_uid,
                c.meta_json, d.path AS deck_path
            FROM cards c
            JOIN scheduling s ON s.card_id = c.id
            JOIN decks d ON d.id = c.deck_id
            WHERE s.due <= ?
              AND COALESCE(json_extract(c.meta_json, '$.status'), 'active') != 'suspended'
            ORDER BY s.due ASC
            """,
            (now.isoformat(),),
        ).fetchall()
        return [self._row_to_card(row) for row in rows]

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
        return self._row_to_card(row) if row else None

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
        now = now or datetime.now(UTC)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        row = conn.execute(
            """
            SELECT COUNT(*) AS cnt FROM reviews r
            JOIN scheduling s ON s.card_id = r.card_id
            WHERE s.reps = 1 AND r.reviewed_at >= ?
            """,
            (start.isoformat(),),
        ).fetchone()
        return int(row["cnt"])

    # --- Analytics ---

    def retention_for_days(self, days: int) -> float:
        conn = self.connect()
        since = (datetime.now(UTC) - timedelta(days=days)).isoformat()
        row = conn.execute(
            """
            SELECT
                SUM(CASE WHEN rating >= 3 THEN 1 ELSE 0 END) AS good,
                COUNT(*) AS total
            FROM reviews WHERE reviewed_at >= ?
            """,
            (since,),
        ).fetchone()
        total = int(row["total"])
        if total == 0:
            return 0.0
        return round(100.0 * int(row["good"]) / total, 1)

    def cards_per_day(self, days: int = 7) -> float:
        conn = self.connect()
        since = (datetime.now(UTC) - timedelta(days=days)).isoformat()
        row = conn.execute(
            """
            SELECT COUNT(*) AS cnt FROM reviews WHERE reviewed_at >= ?
            """,
            (since,),
        ).fetchone()
        return round(int(row["cnt"]) / max(days, 1), 1)

    def refresh_concept_mastery(self, concept_id: int) -> None:
        conn = self.connect()
        now = datetime.now(UTC)
        since_7d = (now - timedelta(days=7)).isoformat()
        since_30d = (now - timedelta(days=30)).isoformat()

        stats = conn.execute(
            """
            SELECT
                COUNT(DISTINCT cc.card_id) AS card_count,
                COUNT(r.id) AS reviews_count,
                SUM(CASE WHEN r.reviewed_at >= ? AND r.rating >= 3 THEN 1 ELSE 0 END) AS good_7d,
                SUM(CASE WHEN r.reviewed_at >= ? THEN 1 ELSE 0 END) AS total_7d,
                SUM(CASE WHEN r.reviewed_at >= ? AND r.rating >= 3 THEN 1 ELSE 0 END) AS good_30d,
                SUM(CASE WHEN r.reviewed_at >= ? THEN 1 ELSE 0 END) AS total_30d,
                SUM(CASE WHEN r.rating = 1 THEN 1 ELSE 0 END) AS lapses,
                MAX(r.reviewed_at) AS last_reviewed
            FROM card_concepts cc
            LEFT JOIN reviews r ON r.card_id = cc.card_id
            WHERE cc.concept_id = ?
            """,
            (since_7d, since_7d, since_30d, since_30d, concept_id),
        ).fetchone()

        card_count = int(stats["card_count"] or 0)
        reviews_count = int(stats["reviews_count"] or 0)
        total_7d = int(stats["total_7d"] or 0)
        total_30d = int(stats["total_30d"] or 0)
        good_7d = int(stats["good_7d"] or 0)
        good_30d = int(stats["good_30d"] or 0)
        lapses = int(stats["lapses"] or 0)

        retention_7d = (100.0 * good_7d / total_7d) if total_7d else 0.0
        retention_30d = (100.0 * good_30d / total_30d) if total_30d else 0.0
        exposure = min(1.0, reviews_count / max(card_count * 2, 1))
        lapse_penalty = min(30.0, lapses * 3.0)
        mastery = max(
            0.0,
            min(100.0, retention_7d * 0.5 + retention_30d * 0.3 + exposure * 20 - lapse_penalty),
        )
        weakness = max(0.0, min(100.0, 100.0 - mastery + lapse_penalty))

        conn.execute(
            """
            INSERT INTO concept_mastery (
                concept_id, card_count, reviews_count, retention_7d, retention_30d,
                mastery_score, weakness_score, last_reviewed_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(concept_id) DO UPDATE SET
                card_count = excluded.card_count,
                reviews_count = excluded.reviews_count,
                retention_7d = excluded.retention_7d,
                retention_30d = excluded.retention_30d,
                mastery_score = excluded.mastery_score,
                weakness_score = excluded.weakness_score,
                last_reviewed_at = excluded.last_reviewed_at,
                updated_at = excluded.updated_at
            """,
            (
                concept_id,
                card_count,
                reviews_count,
                retention_7d,
                retention_30d,
                mastery,
                weakness,
                stats["last_reviewed"],
                now.isoformat(),
            ),
        )
        conn.commit()

    def refresh_mastery_for_card(self, card_id: int) -> None:
        conn = self.connect()
        rows = conn.execute(
            "SELECT concept_id FROM card_concepts WHERE card_id = ?",
            (card_id,),
        ).fetchall()
        for row in rows:
            self.refresh_concept_mastery(int(row["concept_id"]))

    def refresh_all_concept_mastery(self) -> None:
        conn = self.connect()
        rows = conn.execute("SELECT id FROM concepts").fetchall()
        for row in rows:
            self.refresh_concept_mastery(int(row["id"]))

    def list_concept_mastery(self) -> list[ConceptMastery]:
        self.refresh_all_concept_mastery()
        conn = self.connect()
        rows = conn.execute(
            """
            SELECT
                cm.concept_id, c.slug, c.label,
                cm.card_count, cm.reviews_count,
                cm.retention_7d, cm.retention_30d,
                cm.mastery_score, cm.weakness_score, cm.last_reviewed_at
            FROM concept_mastery cm
            JOIN concepts c ON c.id = cm.concept_id
            ORDER BY cm.weakness_score DESC, cm.mastery_score ASC
            """
        ).fetchall()
        result = []
        for row in rows:
            last = None
            if row["last_reviewed_at"]:
                last = datetime.fromisoformat(row["last_reviewed_at"])
            result.append(
                ConceptMastery(
                    concept_id=int(row["concept_id"]),
                    slug=row["slug"],
                    label=row["label"],
                    card_count=int(row["card_count"]),
                    reviews_count=int(row["reviews_count"]),
                    retention_7d=float(row["retention_7d"]),
                    retention_30d=float(row["retention_30d"]),
                    mastery_score=float(row["mastery_score"]),
                    weakness_score=float(row["weakness_score"]),
                    last_reviewed_at=last,
                )
            )
        return result

    def get_card_review_history(self, card_id: int, limit: int = 50) -> list[dict[str, Any]]:
        conn = self.connect()
        rows = conn.execute(
            """
            SELECT rating, reviewed_at, reveal_ms, rating_ms,
                   retrievability, stability, difficulty, state
            FROM reviews WHERE card_id = ?
            ORDER BY reviewed_at DESC LIMIT ?
            """,
            (card_id, limit),
        ).fetchall()
        return [dict(row) for row in rows]

    def count_lapses_for_concept(self, concept_slug: str, days: int = 7) -> int:
        conn = self.connect()
        since = (datetime.now(UTC) - timedelta(days=days)).isoformat()
        row = conn.execute(
            """
            SELECT COUNT(*) AS cnt FROM reviews r
            JOIN card_concepts cc ON cc.card_id = r.card_id
            JOIN concepts c ON c.id = cc.concept_id
            WHERE c.slug = ? AND r.rating = 1 AND r.reviewed_at >= ?
            """,
            (concept_slug, since),
        ).fetchone()
        return int(row["cnt"])

    # --- Stats ---

    def count_due(self, now: datetime | None = None) -> int:
        conn = self.connect()
        now = now or datetime.now(UTC)
        row = conn.execute(
            """
            SELECT COUNT(*) AS cnt
            FROM scheduling s
            JOIN cards c ON c.id = s.card_id
            WHERE s.due <= ?
              AND COALESCE(json_extract(c.meta_json, '$.status'), 'active') != 'suspended'
            """,
            (now.isoformat(),),
        ).fetchone()
        return int(row["cnt"])

    def count_new_cards(self) -> int:
        conn = self.connect()
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM scheduling WHERE reps = 0",
        ).fetchone()
        return int(row["cnt"])

    def count_total_cards(self) -> int:
        conn = self.connect()
        row = conn.execute("SELECT COUNT(*) AS cnt FROM cards").fetchone()
        return int(row["cnt"])

    def count_reviewed_today(self, now: datetime | None = None) -> int:
        conn = self.connect()
        now = now or datetime.now(UTC)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM reviews WHERE reviewed_at >= ?",
            (start.isoformat(),),
        ).fetchone()
        return int(row["cnt"])

    def retention_pct(self) -> float:
        return self.retention_for_days(3650)

    def streak_days(self, now: datetime | None = None) -> int:
        conn = self.connect()
        now = now or datetime.now(UTC)
        rows = conn.execute(
            """
            SELECT DISTINCT date(reviewed_at) AS review_day
            FROM reviews ORDER BY review_day DESC
            """
        ).fetchall()
        if not rows:
            return 0

        from datetime import date

        streak = 0
        expected = now.date()
        for row in rows:
            review_day = date.fromisoformat(row["review_day"])
            if review_day == expected:
                streak += 1
                expected = expected.fromordinal(expected.toordinal() - 1)
            elif streak == 0 and review_day == expected.fromordinal(expected.toordinal() - 1):
                expected = review_day
                streak += 1
                expected = expected.fromordinal(expected.toordinal() - 1)
            else:
                break
        return streak

    def list_decks(self, now: datetime | None = None) -> list[DeckSummary]:
        conn = self.connect()
        now = now or datetime.now(UTC)
        rows = conn.execute(
            """
            SELECT d.id, d.path,
                COUNT(c.id) AS card_count,
                SUM(CASE WHEN s.due <= ? THEN 1 ELSE 0 END) AS due_count
            FROM decks d
            LEFT JOIN cards c ON c.deck_id = d.id
            LEFT JOIN scheduling s ON s.card_id = c.id
            GROUP BY d.id, d.path ORDER BY d.path
            """,
            (now.isoformat(),),
        ).fetchall()
        return [
            DeckSummary(
                id=int(row["id"]),
                path=row["path"],
                card_count=int(row["card_count"]),
                due_count=int(row["due_count"] or 0),
            )
            for row in rows
        ]

    def get_last_import_path(self) -> str | None:
        conn = self.connect()
        row = conn.execute(
            "SELECT source_file FROM collections ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if row:
            return str(row["source_file"])
        row = conn.execute("SELECT source_file FROM decks ORDER BY id DESC LIMIT 1").fetchone()
        return row["source_file"] if row else None

    @staticmethod
    def _card_meta(card: ParsedCard) -> dict[str, Any]:
        meta = dict(card.meta)
        meta.update(
            {
                "status": card.status,
                "links": card.links,
                "hint": card.hint,
                "notes": card.notes,
                "source": card.source,
                "priority": card.priority,
                "concepts": card.concepts,
                "prerequisites": card.prerequisites,
                "difficulty": card.difficulty,
                "objective": card.objective,
            }
        )
        return {k: v for k, v in meta.items() if v is not None}

    @staticmethod
    def _row_to_card(row: sqlite3.Row) -> CardRow:
        meta_raw = row["meta_json"] if "meta_json" in row else "{}"
        meta = json.loads(meta_raw) if meta_raw else {}
        return CardRow(
            id=int(row["id"]),
            deck_id=int(row["deck_id"]),
            front_md=row["front_md"],
            back_md=row["back_md"],
            card_type=row["card_type"],
            tags=json.loads(row["tags_json"]),
            source_line=int(row["source_line"]),
            card_index=int(row["card_index"]),
            deck_path=row["deck_path"],
            card_uid=row["card_uid"] if "card_uid" in row else None,
            hint=meta.get("hint"),
            links=meta.get("links") or [],
            status=meta.get("status") or "active",
            priority=meta.get("priority") or "normal",
        )
