from __future__ import annotations

from pathlib import Path

import pytest

from deckflow.db.repository import Repository
from deckflow.models.domain import ReviewFocus
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
