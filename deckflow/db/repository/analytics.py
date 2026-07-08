from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any

from deckflow.models.domain import ConceptMastery, DeckSummary


class AnalyticsMixin:
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
