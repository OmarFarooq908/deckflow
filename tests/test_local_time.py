from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from deckflow.db.repository import Repository
from deckflow.local_time import local_day_start, local_today
from deckflow.service.import_service import import_deck

ADVANCED = Path(__file__).parent.parent / "examples" / "legacy" / "advanced_sample_deck.md"


@pytest.fixture()
def repo(tmp_path: Path) -> Repository:
    repository = Repository(tmp_path / "local_time.db")
    repository.initialize()
    return repository


def _insert_review(repo: Repository, card_id: int, reviewed_at: datetime) -> None:
    conn = repo.connect()
    conn.execute(
        """
        INSERT INTO reviews (card_id, rating, reviewed_at, retrievability, state)
        VALUES (?, 3, ?, 0.9, 2)
        """,
        (card_id, reviewed_at.isoformat()),
    )
    conn.commit()


@pytest.fixture()
def eastern_tz(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DECKFLOW_TZ", "America/New_York")


def test_count_reviewed_today_uses_local_midnight(repo: Repository, eastern_tz: None) -> None:
    import_deck(repo, ADVANCED)
    card_id = repo.get_due_candidates()[0].id
    # July 8 22:00 EDT = July 9 02:00 UTC
    _insert_review(repo, card_id, datetime(2026, 7, 9, 2, 0, tzinfo=UTC))
    # Still July 8 locally (23:00 EDT)
    now = datetime(2026, 7, 9, 3, 0, tzinfo=UTC)
    assert repo.count_reviewed_today(now) == 1
    assert repo.count_reviewed_today(datetime(2026, 7, 9, 4, 0, tzinfo=UTC)) == 0


def test_count_new_cards_today_uses_local_midnight(repo: Repository, eastern_tz: None) -> None:
    import_deck(repo, ADVANCED)
    card_id = repo.get_due_candidates()[0].id
    conn = repo.connect()
    conn.execute("UPDATE scheduling SET reps = 1 WHERE card_id = ?", (card_id,))
    conn.commit()
    _insert_review(repo, card_id, datetime(2026, 7, 9, 2, 0, tzinfo=UTC))
    now = datetime(2026, 7, 9, 3, 0, tzinfo=UTC)
    assert repo.count_new_cards_today(now) == 1


def test_streak_counts_local_calendar_days(repo: Repository, eastern_tz: None) -> None:
    import_deck(repo, ADVANCED)
    cards = repo.get_due_candidates()
    # Two reviews on consecutive local days near UTC boundary
    _insert_review(repo, cards[0].id, datetime(2026, 7, 9, 2, 0, tzinfo=UTC))  # July 8 local
    _insert_review(repo, cards[1].id, datetime(2026, 7, 9, 6, 0, tzinfo=UTC))  # July 9 local
    now = datetime(2026, 7, 9, 10, 0, tzinfo=UTC)
    assert repo.streak_days(now) == 2


def test_local_day_start_is_timezone_aware() -> None:
    now = datetime(2026, 7, 9, 15, 30, tzinfo=UTC)
    start = local_day_start(now)
    assert start.tzinfo is not None
    assert local_today(now).isoformat() == "2026-07-09"
