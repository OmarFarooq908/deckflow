from __future__ import annotations

from datetime import UTC, datetime


class ReviewsMixin:
    def get_or_create_session(self, collection_id: int | None = None) -> int:
        session_id = self._active_session_id
        if session_id is not None:
            return session_id
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
        return int(lastrowid)

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
