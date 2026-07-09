from pathlib import Path

import pytest

from deckflow.db.repository import Repository
from deckflow.models.domain import ReviewTelemetry
from deckflow.parser.markdown import parse_markdown_deck
from deckflow.service.analytics_service import get_overview, get_study_plan, get_weak_spots
from deckflow.service.import_service import import_deck
from deckflow.service.queue_service import build_daily_queue
from deckflow.service.review_service import submit_review

ADVANCED = Path(__file__).parent.parent / "examples" / "legacy" / "advanced_sample_deck.md"
V2_PROJECT = Path(__file__).parent.parent / "examples" / "python-de-interview"


@pytest.fixture()
def repo(tmp_path: Path) -> Repository:
    db_path = tmp_path / "analytics.db"
    repository = Repository(db_path)
    repository.initialize()
    return repository


def test_v11_concepts_and_objective_parsed() -> None:
    cards = parse_markdown_deck(ADVANCED)
    card = next(c for c in cards if c.card_uid == "py-001")
    assert "python::fundamentals" in card.concepts
    assert card.difficulty == 2
    assert card.objective is not None


def test_review_telemetry_persisted(repo: Repository) -> None:
    import_deck(repo, ADVANCED)
    card = repo.get_due_candidates()[0]
    submit_review(
        repo,
        card.id,
        rating=3,
        telemetry=ReviewTelemetry(reveal_ms=1200, rating_ms=800),
    )
    history = repo.get_card_review_history(card.id)
    assert len(history) == 1
    assert history[0]["reveal_ms"] == 1200
    assert history[0]["rating_ms"] == 800
    assert history[0]["retrievability"] is not None
    assert history[0]["state"] is not None


def test_smart_queue_returns_reason(repo: Repository) -> None:
    import_deck(repo, ADVANCED)
    queue = build_daily_queue(repo, limit=5)
    assert len(queue) > 0
    assert queue[0].reason
    assert queue[0].score > 0


def test_analytics_overview_after_reviews(repo: Repository) -> None:
    import_deck(repo, ADVANCED)
    card = repo.get_due_candidates()[0]
    submit_review(repo, card.id, rating=3)
    overview = get_overview(repo)
    assert overview.total_cards == 12
    assert overview.reviewed_today >= 1


def test_study_plan_lists_cards(repo: Repository) -> None:
    import_deck(repo, ADVANCED)
    plan = get_study_plan(repo, limit=5)
    assert len(plan) > 0
    assert plan[0].reason


def test_concept_mastery_computed(repo: Repository) -> None:
    import_deck(repo, ADVANCED)
    card = repo.get_due_candidates()[0]
    submit_review(repo, card.id, rating=3)
    concepts = repo.list_concept_mastery()
    assert len(concepts) > 0


def test_weak_spots_after_lapse(repo: Repository) -> None:
    import_deck(repo, ADVANCED)
    card = repo.get_due_candidates()[0]
    submit_review(repo, card.id, rating=1)
    spots = get_weak_spots(repo, limit=5)
    assert isinstance(spots, list)


def test_list_decks_excludes_suspended_from_due_count(repo: Repository) -> None:
    from deckflow.models.domain import ParsedCard

    deck_id = repo.upsert_deck("Test::Suspended", "test")
    repo.upsert_card(
        deck_id,
        ParsedCard(
            deck_path="Test::Suspended",
            card_index=1001,
            source_line=1,
            front_md="active",
            back_md="answer",
            card_uid="active-card",
        ),
    )
    repo.upsert_card(
        deck_id,
        ParsedCard(
            deck_path="Test::Suspended",
            card_index=1002,
            source_line=1,
            front_md="suspended",
            back_md="answer",
            card_uid="suspended-card",
            status="suspended",
        ),
    )

    deck = next(item for item in repo.list_decks() if item.id == deck_id)
    assert deck.card_count == 2
    assert deck.due_count == 1
    assert repo.count_due() == 1
