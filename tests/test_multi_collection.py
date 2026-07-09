from __future__ import annotations

from pathlib import Path

import pytest

from deckflow.db.repository import Repository
from deckflow.models.domain import ParsedCard
from deckflow.service.library_service import build_collection_summaries, build_track_summaries
from deckflow.service.queue_service import build_daily_queue
from deckflow.service.review_service import submit_review


@pytest.fixture()
def repo(tmp_path: Path) -> Repository:
    repository = Repository(tmp_path / "multi_collection.db")
    repository.initialize()
    return repository


def _add_collection(
    repo: Repository,
    slug: str,
    *,
    max_reviews: int,
    tracks: list[dict] | None = None,
) -> int:
    return repo.upsert_collection(
        slug=slug,
        title=slug.replace("-", " ").title(),
        source_file=f"test::{slug}",
        config={"new_per_day": 20, "max_reviews_per_day": max_reviews},
        meta={"tracks": tracks or []},
    )


def _add_card(repo: Repository, collection_id: int, slug: str) -> int:
    deck_id = repo.upsert_deck(
        f"{slug}::Deck",
        f"test::{slug}",
        collection_id=collection_id,
    )
    return repo.upsert_card(
        deck_id,
        ParsedCard(
            deck_path=f"{slug}::Deck",
            card_index=abs(hash(slug)) % 1_000_000,
            source_line=1,
            front_md=f"front {slug}",
            back_md=f"back {slug}",
            card_uid=slug,
        ),
    )


def test_collection_summaries_use_scoped_counts(repo: Repository) -> None:
    first = _add_collection(repo, "alpha", max_reviews=10)
    second = _add_collection(repo, "beta", max_reviews=10)
    _add_card(repo, first, "alpha-card")
    _add_card(repo, second, "beta-card")
    _add_card(repo, second, "beta-card-2")

    summaries = build_collection_summaries(repo)
    by_slug = {item.slug: item for item in summaries}
    assert by_slug["alpha"].card_count == 1
    assert by_slug["beta"].card_count == 2
    assert by_slug["alpha"].due_count == 1
    assert by_slug["beta"].due_count == 2


def test_track_summaries_include_all_collections(repo: Repository) -> None:
    _add_collection(
        repo,
        "alpha",
        max_reviews=10,
        tracks=[{"id": "alpha-track", "title": "Alpha Track", "steps": []}],
    )
    _add_collection(
        repo,
        "beta",
        max_reviews=10,
        tracks=[{"id": "beta-track", "title": "Beta Track", "steps": []}],
    )

    tracks = build_track_summaries(repo)
    track_ids = {track.id for track in tracks}
    assert "alpha::alpha-track" in track_ids
    assert "beta::beta-track" in track_ids


def test_per_collection_review_caps(repo: Repository) -> None:
    first = _add_collection(repo, "alpha", max_reviews=1)
    second = _add_collection(repo, "beta", max_reviews=1)
    alpha_card = _add_card(repo, first, "alpha-card")
    beta_card = _add_card(repo, second, "beta-card")

    queue = build_daily_queue(repo, limit=10)
    assert len(queue) == 2

    submit_review(repo, alpha_card, rating=3)
    queue = build_daily_queue(repo, limit=10)
    assert len(queue) == 1
    assert queue[0].card.id == beta_card


def test_deck_config_uses_own_collection(repo: Repository) -> None:
    first = _add_collection(repo, "alpha", max_reviews=10)
    _add_collection(repo, "beta", max_reviews=10)
    deck_id = repo.upsert_deck(
        "Alpha::Deck",
        "test::alpha",
        meta={"config": {"new_per_day": 3}},
        collection_id=first,
    )
    repo.upsert_card(
        deck_id,
        ParsedCard(
            deck_path="Alpha::Deck",
            card_index=1,
            source_line=1,
            front_md="front",
            back_md="back",
            card_uid="alpha-only",
        ),
    )

    config = repo.get_scheduling_config_for_deck(deck_id)
    assert config["new_per_day"] == 3
    assert config["max_reviews_per_day"] == 10


def test_imported_collections_keep_isolated_stats(repo: Repository) -> None:
    first = _add_collection(repo, "alpha", max_reviews=10)
    second = _add_collection(repo, "beta", max_reviews=10)
    _add_card(repo, first, "alpha-card")
    _add_card(repo, second, "beta-card")
    _add_card(repo, second, "beta-card-2")

    summaries = build_collection_summaries(repo)
    assert len(summaries) == 2
    assert sum(item.card_count for item in summaries) == repo.count_total_cards()
