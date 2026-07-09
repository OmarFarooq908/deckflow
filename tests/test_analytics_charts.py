from pathlib import Path

import pytest

from deckflow.db.repository import Repository
from deckflow.service.analytics_service import get_dashboard
from deckflow.service.import_service import import_deck
from deckflow.service.review_service import submit_review

ADVANCED = Path(__file__).parent.parent / "examples" / "legacy" / "advanced_sample_deck.md"


@pytest.fixture()
def repo(tmp_path: Path) -> Repository:
    db_path = tmp_path / "charts.db"
    repository = Repository(db_path)
    repository.initialize()
    return repository


def _seed_reviews(repo: Repository, ratings: list[int]) -> None:
    import_deck(repo, ADVANCED)
    candidates = repo.get_due_candidates()
    for i, rating in enumerate(ratings):
        card = candidates[i % len(candidates)]
        submit_review(repo, card.id, rating=rating)


def test_daily_activity_after_reviews(repo: Repository) -> None:
    _seed_reviews(repo, [3, 3, 1, 4])
    activity = repo.daily_activity(days=30)
    assert len(activity) >= 1
    total_reviews = sum(row["reviews"] for row in activity)
    assert total_reviews == 4
    total_good = sum(row["good"] for row in activity)
    assert total_good == 3
    total_again = sum(row["again"] for row in activity)
    assert total_again == 1


def test_retention_trend_after_reviews(repo: Repository) -> None:
    _seed_reviews(repo, [3, 2, 3])
    trend = repo.retention_trend(weeks=12)
    assert len(trend) >= 1
    assert trend[-1]["reviews"] == 3
    assert trend[-1]["retention_pct"] == pytest.approx(66.7, abs=0.1)


def test_rating_distribution(repo: Repository) -> None:
    _seed_reviews(repo, [1, 2, 3, 4, 3])
    ratings = repo.rating_distribution(days=30)
    by_label = {row["label"]: row["count"] for row in ratings}
    assert by_label["Again"] == 1
    assert by_label["Hard"] == 1
    assert by_label["Good"] == 2
    assert by_label["Easy"] == 1


def test_deck_workload_by_prefix(repo: Repository) -> None:
    import_deck(repo, ADVANCED)
    workload = repo.deck_workload_by_prefix(depth=2)
    assert len(workload) >= 1
    assert all("label" in row and "due" in row and "total" in row for row in workload)
    assert sum(row["total"] for row in workload) == 12


def test_avg_retrievability_trend(repo: Repository) -> None:
    _seed_reviews(repo, [3, 3])
    trend = repo.avg_retrievability_trend(days=30)
    assert len(trend) >= 1
    assert 0 <= trend[-1]["avg_retrievability"] <= 1


def test_get_dashboard_shape(repo: Repository) -> None:
    _seed_reviews(repo, [3, 1, 4])
    dashboard = get_dashboard(repo)
    assert dashboard.overview.total_cards == 12
    assert dashboard.overview.reviewed_today >= 3
    assert len(dashboard.activity) >= 1
    assert len(dashboard.retention_trend) >= 1
    assert len(dashboard.ratings) >= 1
    assert len(dashboard.deck_workload) >= 1
