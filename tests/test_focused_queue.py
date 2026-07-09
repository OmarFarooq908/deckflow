from __future__ import annotations

from pathlib import Path

import pytest

from deckflow.db.repository import Repository
from deckflow.models.domain import ParsedCard, ReviewFocus
from deckflow.service.import_service import import_deck
from deckflow.service.queue_service import build_daily_queue
from deckflow.service.review_service import get_next_card

V2_PROJECT = Path(__file__).parent.parent / "examples" / "python-de-interview"
ADVANCED = Path(__file__).parent.parent / "examples" / "legacy" / "advanced_sample_deck.md"
FIXTURE = Path(__file__).parent / "fixtures" / "sample_deck.md"


@pytest.fixture()
def repo(tmp_path: Path) -> Repository:
    repository = Repository(tmp_path / "focus.db")
    repository.initialize()
    return repository


def test_filter_by_deck_prefix(repo: Repository) -> None:
    import_deck(repo, V2_PROJECT)
    focus = ReviewFocus(deck_prefix="Python::01 Fundamentals")
    queue = build_daily_queue(repo, limit=50, focus=focus)
    assert queue
    for item in queue:
        assert item.card.deck_path.startswith("Python::01 Fundamentals")


def test_filter_by_concept_slug(repo: Repository) -> None:
    import_deck(repo, ADVANCED)
    focus = ReviewFocus(concept_slug="python::fundamentals")
    queue = build_daily_queue(repo, limit=50, focus=focus)
    assert queue
    for item in queue:
        slugs = repo.get_card_concept_slugs(item.card.id)
        assert "python::fundamentals" in slugs


def test_focus_appends_queue_reason(repo: Repository) -> None:
    import_deck(repo, FIXTURE)
    focus = ReviewFocus(deck_prefix="Sample::Basics")
    queue = build_daily_queue(repo, limit=5, focus=focus)
    assert queue
    assert "focused:" in queue[0].reason


def test_review_order_deck_sorts_by_path(repo: Repository) -> None:
    import_deck(repo, V2_PROJECT)
    queue = build_daily_queue(repo, limit=20)
    paths = [item.card.deck_path for item in queue]
    assert paths == sorted(paths)


def test_get_next_card_with_focus(repo: Repository) -> None:
    import_deck(repo, FIXTURE)
    focus = ReviewFocus(deck_prefix="Sample::Basics")
    card, reason = get_next_card(repo, focus=focus)
    assert card is not None
    assert card.deck_path.startswith("Sample::Basics")
    assert reason and "focused:" in reason


def test_concept_fatigue_deprioritizes_shared_concepts(repo: Repository) -> None:
    deck_id = repo.upsert_deck("Test::Fatigue", "test")
    shared = ParsedCard(
        deck_path="Test::Fatigue",
        card_index=1001,
        source_line=1,
        front_md="shared question",
        back_md="shared answer",
        card_uid="fatigue-shared-a",
        concepts=["shared::concept"],
    )
    shared_sibling = ParsedCard(
        deck_path="Test::Fatigue",
        card_index=1002,
        source_line=1,
        front_md="shared question 2",
        back_md="shared answer 2",
        card_uid="fatigue-shared-b",
        concepts=["shared::concept"],
    )
    other = ParsedCard(
        deck_path="Test::Fatigue",
        card_index=1003,
        source_line=1,
        front_md="other question",
        back_md="other answer",
        card_uid="fatigue-other",
        concepts=["other::concept"],
    )
    repo.upsert_card(deck_id, shared)
    repo.upsert_card(deck_id, shared_sibling)
    repo.upsert_card(deck_id, other)

    queue = build_daily_queue(repo, limit=2)
    fronts = [item.card.front_md for item in queue]

    assert len(fronts) == 2
    assert "other question" in fronts
    assert fronts[0] in {"shared question", "shared question 2"}
    assert fronts[1] == "other question"


def test_concept_fatigue_applies_during_scoring(repo: Repository) -> None:
    import_deck(repo, ADVANCED)
    from deckflow.service import queue_service

    sizes_at_call: list[int] = []
    original = queue_service._concept_fatigue

    def capture(card_id: int, repo: Repository, recent: list[str]) -> float:
        sizes_at_call.append(len(recent))
        return original(card_id, repo, recent)

    queue_service._concept_fatigue = capture
    try:
        queue_service.build_daily_queue(repo, limit=3)
    finally:
        queue_service._concept_fatigue = original

    assert any(size > 0 for size in sizes_at_call)
