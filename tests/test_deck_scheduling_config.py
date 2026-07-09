from __future__ import annotations

from pathlib import Path

import pytest

from deckflow.db.repository import Repository
from deckflow.models.domain import ParsedCard
from deckflow.service.import_service import import_deck
from deckflow.service.queue_service import build_daily_queue
from deckflow.service.review_service import submit_review

ADVANCED = Path(__file__).parent.parent / "examples" / "legacy" / "advanced_sample_deck.md"
FIXTURE = Path(__file__).parent / "fixtures" / "sample_deck.md"


@pytest.fixture()
def repo(tmp_path: Path) -> Repository:
    repository = Repository(tmp_path / "deck_config.db")
    repository.initialize()
    return repository


def _add_new_card(repo: Repository, deck_id: int, deck_path: str, uid: str) -> int:
    return repo.upsert_card(
        deck_id,
        ParsedCard(
            deck_path=deck_path,
            card_index=abs(hash(uid)) % 1_000_000,
            source_line=1,
            front_md=f"front {uid}",
            back_md=f"back {uid}",
            card_uid=uid,
        ),
    )


def test_deck_new_per_day_zero_excludes_new_cards(repo: Repository) -> None:
    collection_id = repo.upsert_collection(
        slug="sched-test",
        title="Sched Test",
        source_file="test",
        config={"new_per_day": 20, "max_reviews_per_day": 150},
    )
    deck_id = repo.upsert_deck(
        "Blocked::Deck",
        "test",
        meta={"config": {"new_per_day": 0}},
        collection_id=collection_id,
    )
    _add_new_card(repo, deck_id, "Blocked::Deck", "blocked-1")

    queue = build_daily_queue(repo, limit=10)
    assert queue == []


def test_deck_new_per_day_caps_new_cards_per_deck(repo: Repository) -> None:
    collection_id = repo.upsert_collection(
        slug="sched-test",
        title="Sched Test",
        source_file="test",
        config={"new_per_day": 20, "max_reviews_per_day": 150},
    )
    deck_a = repo.upsert_deck(
        "A::Deck",
        "test",
        meta={"config": {"new_per_day": 1}},
        collection_id=collection_id,
    )
    deck_b = repo.upsert_deck(
        "B::Deck",
        "test",
        meta={"config": {"new_per_day": 1}},
        collection_id=collection_id,
    )
    _add_new_card(repo, deck_a, "A::Deck", "a-1")
    _add_new_card(repo, deck_a, "A::Deck", "a-2")
    _add_new_card(repo, deck_b, "B::Deck", "b-1")
    _add_new_card(repo, deck_b, "B::Deck", "b-2")

    queue = build_daily_queue(repo, limit=10)
    new_cards = [item for item in queue if repo.get_scheduling(item.card.id).reps == 0]
    assert len(new_cards) == 2
    deck_paths = {item.card.deck_path for item in new_cards}
    assert deck_paths == {"A::Deck", "B::Deck"}


def test_deck_new_per_day_from_imported_metadata(repo: Repository) -> None:
    import_deck(repo, ADVANCED)
    variables_prefix = "Python::01 Fundamentals::Variables & Types"
    variables_deck = next(deck for deck in repo.list_decks() if deck.path == variables_prefix)
    config = repo.get_scheduling_config_for_deck(variables_deck.id)
    assert config["new_per_day"] == 10

    queue = build_daily_queue(repo, limit=50)
    new_from_variables = [
        item
        for item in queue
        if item.card.deck_path == variables_prefix and repo.get_scheduling(item.card.id).reps == 0
    ]
    assert len(new_from_variables) <= 10


def test_reviewing_new_card_consumes_deck_budget(repo: Repository) -> None:
    collection_id = repo.upsert_collection(
        slug="sched-test",
        title="Sched Test",
        source_file="test",
        config={"new_per_day": 20, "max_reviews_per_day": 150},
    )
    deck_id = repo.upsert_deck(
        "A::Deck",
        "test",
        meta={"config": {"new_per_day": 1}},
        collection_id=collection_id,
    )
    _add_new_card(repo, deck_id, "A::Deck", "a-1")
    _add_new_card(repo, deck_id, "A::Deck", "a-2")

    queue = build_daily_queue(repo, limit=10)
    assert len(queue) == 1
    submit_review(repo, queue[0].card.id, rating=3)

    queue = build_daily_queue(repo, limit=10)
    new_cards = [item for item in queue if repo.get_scheduling(item.card.id).reps == 0]
    assert len(new_cards) == 0


def test_collection_new_per_day_still_defaults_without_deck_override(repo: Repository) -> None:
    import_deck(repo, FIXTURE)
    config = repo.get_scheduling_config_for_deck(repo.get_due_candidates()[0].deck_id)
    assert config.get("new_per_day", 20) >= 1
