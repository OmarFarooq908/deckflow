from __future__ import annotations

from datetime import UTC, datetime

from deckflow.db.repository import Repository
from deckflow.models.domain import DeckSummary, Stats


def get_stats(repo: Repository) -> Stats:
    now = datetime.now(UTC)
    return Stats(
        due_today=repo.count_due(now),
        new_cards=repo.count_new_cards(),
        reviewed_today=repo.count_reviewed_today(now),
        total_cards=repo.count_total_cards(),
        retention_pct=repo.retention_pct(),
        streak_days=repo.streak_days(now),
    )


def get_decks(repo: Repository) -> list[DeckSummary]:
    return repo.list_decks(datetime.now(UTC))


def get_last_import_path(repo: Repository) -> str | None:
    return repo.get_last_import_path()
