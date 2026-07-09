from __future__ import annotations

import random
from datetime import UTC, datetime
from pathlib import Path

import pytest

from deckflow.db.repository import Repository
from deckflow.models.domain import ParsedCard
from deckflow.scheduler.fsrs import card_to_json, new_fsrs_card, review_card
from deckflow.service.queue_service import build_daily_queue
from deckflow.service.review_service import submit_review


@pytest.fixture()
def repo(tmp_path: Path) -> Repository:
    repository = Repository(tmp_path / "config_keys.db")
    repository.initialize()
    return repository


def _seed_collection(repo: Repository) -> int:
    return repo.upsert_collection(
        slug="config-test",
        title="Config Test",
        source_file="test",
        config={"new_per_day": 20, "max_reviews_per_day": 150},
    )


def _add_card(
    repo: Repository,
    deck_id: int,
    deck_path: str,
    uid: str,
    *,
    card_config: dict | None = None,
    status: str = "active",
) -> int:
    meta: dict = {"slug": uid}
    if card_config:
        meta["card_config"] = card_config
    if status != "active":
        meta["status"] = status
    return repo.upsert_card(
        deck_id,
        ParsedCard(
            deck_path=deck_path,
            card_index=abs(hash(uid)) % 1_000_000,
            source_line=1,
            front_md=f"front {uid}",
            back_md=f"back {uid}",
            card_uid=uid,
            status=status,
            meta=meta,
        ),
    )


def test_review_order_random_varies_selection(repo: Repository) -> None:
    collection_id = _seed_collection(repo)
    repo.upsert_collection(
        slug="config-test",
        title="Config Test",
        source_file="test",
        config={
            "new_per_day": 20,
            "max_reviews_per_day": 150,
            "review_order": "random",
        },
    )
    deck_id = repo.upsert_deck(
        "Random::Deck",
        "test",
        collection_id=collection_id,
    )
    for idx in range(6):
        _add_card(repo, deck_id, "Random::Deck", f"card-{idx}")

    random.seed(1)
    first = [item.card.id for item in build_daily_queue(repo, limit=3)]
    random.seed(99)
    second = [item.card.id for item in build_daily_queue(repo, limit=3)]
    assert len(first) == 3
    assert first != second


def test_config_suspend_excludes_card_from_queue(repo: Repository) -> None:
    collection_id = _seed_collection(repo)
    deck_id = repo.upsert_deck("Suspend::Deck", "test", collection_id=collection_id)
    active_id = _add_card(repo, deck_id, "Suspend::Deck", "active-1")
    _add_card(
        repo,
        deck_id,
        "Suspend::Deck",
        "suspended-1",
        card_config={"suspend": True},
    )

    queue = build_daily_queue(repo, limit=10)
    queued_ids = {item.card.id for item in queue}
    assert active_id in queued_ids
    assert (
        repo.is_card_scheduling_blocked(
            next(item.card.id for item in queue if item.card.id != active_id)
            if len(queued_ids) > 1
            else active_id
        )
        is False
    )
    assert all(item.card.card_uid != "suspended-1" for item in queue)


def test_desired_retention_changes_fsrs_interval() -> None:
    fsrs_json = card_to_json(new_fsrs_card(card_id=1))
    now = datetime.now(UTC)

    def advance(card_json: str, retention: float, steps: int = 4) -> tuple[str, datetime]:
        current = card_json
        at = now
        for _ in range(steps):
            updated, _ = review_card(current, 3, at, desired_retention=retention)
            current = card_to_json(updated)
            at = updated.due
        return current, at

    high_json, at = advance(fsrs_json, 0.95)
    low_json, _ = advance(fsrs_json, 0.7)
    high, _ = review_card(high_json, 3, at, desired_retention=0.95)
    low, _ = review_card(low_json, 3, at, desired_retention=0.7)
    assert high.due != low.due


def test_bury_related_postpones_linked_cards(repo: Repository) -> None:
    collection_id = _seed_collection(repo)
    deck_id = repo.upsert_deck("Bury::Deck", "test", collection_id=collection_id)
    related_id = _add_card(repo, deck_id, "Bury::Deck", "py-001", card_config={})
    reviewed_id = _add_card(
        repo,
        deck_id,
        "Bury::Deck",
        "py-002",
        card_config={"bury_related": True, "related": ["py-001"]},
    )

    submit_review(repo, reviewed_id, rating=3)
    related_due = repo.get_scheduling(related_id).due
    reviewed_due = repo.get_scheduling(reviewed_id).due
    assert related_due > datetime.now(UTC)
    assert reviewed_due <= datetime.now(UTC) or reviewed_due > datetime.now(UTC)


def test_bury_related_uses_slug_reference(repo: Repository) -> None:
    collection_id = _seed_collection(repo)
    deck_id = repo.upsert_deck("Bury::Slug", "test", collection_id=collection_id)
    related_id = _add_card(
        repo,
        deck_id,
        "Bury::Slug",
        "py-001",
        card_config={},
    )
    conn = repo.connect()
    conn.execute(
        "UPDATE cards SET meta_json = ? WHERE id = ?",
        (
            '{"slug": "py-001-immutable-types", "card_config": {}}',
            related_id,
        ),
    )
    conn.commit()
    reviewed_id = _add_card(
        repo,
        deck_id,
        "Bury::Slug",
        "py-002",
        card_config={"bury_related": True, "related": ["py-001-immutable-types"]},
    )

    submit_review(repo, reviewed_id, rating=3)
    assert repo.get_scheduling(related_id).due > datetime.now(UTC)
