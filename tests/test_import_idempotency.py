from pathlib import Path

import pytest

from deckflow.db.repository import Repository
from deckflow.service.import_service import import_deck
from deckflow.service.review_service import submit_review

FIXTURE = Path(__file__).parent / "fixtures" / "sample_deck.md"


@pytest.fixture()
def repo(tmp_path: Path) -> Repository:
    db_path = tmp_path / "test.db"
    repository = Repository(db_path)
    repository.initialize()
    return repository


def test_import_idempotency(repo: Repository) -> None:
    first = import_deck(repo, FIXTURE)
    second = import_deck(repo, FIXTURE)

    assert first["imported"] == 3
    assert second["imported"] == 3
    assert repo.count_total_cards() == 3


def test_v2_project_import_idempotency(repo: Repository) -> None:
    project = Path(__file__).parent.parent / "examples" / "python-de-interview"
    first = import_deck(repo, project)
    second = import_deck(repo, project)
    assert first["imported"] == 12
    assert second["imported"] == 12
    assert repo.count_total_cards() == 12


def test_review_preserves_card_count_on_reimport(repo: Repository) -> None:
    import_deck(repo, FIXTURE)
    card = repo.get_due_cards(limit=1)[0]
    submit_review(repo, card.id, rating=3)

    import_deck(repo, FIXTURE)
    assert repo.count_total_cards() == 3
    scheduling = repo.get_scheduling(card.id)
    assert scheduling is not None
    assert scheduling.reps == 1


def test_reimport_replaces_stale_concept_links(repo: Repository) -> None:
    from deckflow.models.domain import ParsedCard

    deck_id = repo.upsert_deck("Test::Concepts", "test")
    card = ParsedCard(
        deck_path="Test::Concepts",
        card_index=1001,
        source_line=1,
        front_md="question",
        back_md="answer",
        card_uid="concept-sync-test",
        concepts=["alpha"],
    )
    card_id = repo.upsert_card(deck_id, card)
    assert repo.get_card_concept_slugs(card_id) == ["alpha"]

    updated = ParsedCard(
        deck_path="Test::Concepts",
        card_index=1001,
        source_line=1,
        front_md="question",
        back_md="answer",
        card_uid="concept-sync-test",
        concepts=["beta"],
    )
    repo.upsert_card(deck_id, updated)
    assert repo.get_card_concept_slugs(card_id) == ["beta"]


def test_reimport_clears_concept_links_when_removed(repo: Repository) -> None:
    from deckflow.models.domain import ParsedCard

    deck_id = repo.upsert_deck("Test::Concepts", "test")
    card = ParsedCard(
        deck_path="Test::Concepts",
        card_index=1002,
        source_line=1,
        front_md="question",
        back_md="answer",
        card_uid="concept-clear-test",
        concepts=["alpha"],
    )
    card_id = repo.upsert_card(deck_id, card)

    cleared = ParsedCard(
        deck_path="Test::Concepts",
        card_index=1002,
        source_line=1,
        front_md="question",
        back_md="answer",
        card_uid="concept-clear-test",
        concepts=[],
        tags=["fallback-tag"],
    )
    repo.upsert_card(deck_id, cleared)
    assert repo.get_card_concept_slugs(card_id) == ["fallback-tag"]


def test_reimport_prunes_cards_removed_from_source(repo: Repository) -> None:
    from deckflow.models.domain import ParsedCard

    import_deck(repo, FIXTURE)
    row = repo.connect().execute("SELECT id FROM decks LIMIT 1").fetchone()
    assert row is not None
    deck_id = int(row["id"])

    orphan_id = repo.upsert_card(
        deck_id,
        ParsedCard(
            deck_path="Sample::Basics",
            card_index=999001,
            source_line=1,
            front_md="orphan",
            back_md="gone",
            card_uid="orphan-card",
        ),
    )
    assert repo.count_total_cards() == 4
    assert repo.get_card(orphan_id) is not None

    import_deck(repo, FIXTURE)

    assert repo.count_total_cards() == 3
    assert repo.get_card(orphan_id) is None


def test_reimport_prunes_decks_removed_from_source(repo: Repository) -> None:
    from deckflow.models.domain import ParsedCard

    import_deck(repo, FIXTURE)
    source_row = repo.connect().execute("SELECT source_file FROM decks LIMIT 1").fetchone()
    assert source_row is not None
    source_file = str(source_row["source_file"])

    extra_deck_id = repo.upsert_deck("Sample::Removed", source_file)
    repo.upsert_card(
        extra_deck_id,
        ParsedCard(
            deck_path="Sample::Removed",
            card_index=1,
            source_line=1,
            front_md="orphan deck",
            back_md="gone",
            card_uid="orphan-deck-card",
        ),
    )
    assert repo.count_total_cards() == 4

    import_deck(repo, FIXTURE)

    assert repo.count_total_cards() == 3
    row = (
        repo.connect()
        .execute(
            "SELECT id FROM decks WHERE path = ? AND source_file = ?",
            ("Sample::Removed", source_file),
        )
        .fetchone()
    )
    assert row is None
