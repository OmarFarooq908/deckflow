from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.main import app, clear_repo_cache

FIXTURE = Path(__file__).parent / "fixtures" / "sample_deck.md"
V2_PROJECT = Path(__file__).parent.parent / "examples" / "python-de-interview"
PYTHON_DECK = Path(
    "/Users/dev/Documents/Personal/LeetCode/LeetCode/arb-data-engineer/anki/PYTHON_DECK.md"
)


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    clear_repo_cache()
    db_path = tmp_path / "api.db"
    monkeypatch.setenv("DECKFLOW_DB", str(db_path))
    return TestClient(app)


def test_api_import_review_flow(client: TestClient) -> None:
    response = client.post("/import", json={"path": str(FIXTURE)})
    assert response.status_code == 200
    assert response.json()["imported"] == 3

    stats = client.get("/stats")
    assert stats.status_code == 200
    assert stats.json()["total_cards"] == 3

    card_response = client.get("/review/next")
    assert card_response.status_code == 200
    card = card_response.json()
    assert card is not None

    review_response = client.post(f"/review/{card['id']}", json={"rating": 3})
    assert review_response.status_code == 200
    assert review_response.json()["session_id"] >= 1

    decks = client.get("/decks")
    assert decks.status_code == 200
    assert len(decks.json()) == 1


def test_api_library_and_focused_review(client: TestClient) -> None:
    response = client.post("/import", json={"path": str(V2_PROJECT)})
    assert response.status_code == 200

    library = client.get("/library")
    assert library.status_code == 200
    payload = library.json()
    assert payload["collection"]["slug"] == "python-de-interview"
    assert len(payload["modules"]) >= 1
    assert len(payload["tracks"]) >= 1

    modules_only = client.get("/library/modules")
    assert modules_only.status_code == 200
    assert len(modules_only.json()) >= 1

    topics = client.get("/library/topics")
    assert topics.status_code == 200

    focused = client.get(
        "/review/next",
        params={"deck_prefix": "Python::01 Fundamentals"},
    )
    assert focused.status_code == 200
    card = focused.json()
    if card is not None:
        assert card["deck_path"].startswith("Python::01 Fundamentals")
        assert "concepts" in card

    plan = client.get(
        "/study-plan/today",
        params={"deck_prefix": "Python::01 Fundamentals", "limit": 5},
    )
    assert plan.status_code == 200
    assert isinstance(plan.json(), list)


def test_api_review_session_persists_across_requests(client: TestClient) -> None:
    client.post("/import", json={"path": str(FIXTURE)})

    session_ids: list[int] = []
    for _ in range(3):
        card_response = client.get("/review/next")
        card = card_response.json()
        assert card is not None
        review_response = client.post(f"/review/{card['id']}", json={"rating": 3})
        assert review_response.status_code == 200
        session_ids.append(review_response.json()["session_id"])

    assert len(set(session_ids)) == 1


def test_api_review_session_reset_starts_new_session(client: TestClient) -> None:
    client.post("/import", json={"path": str(FIXTURE)})

    card = client.get("/review/next").json()
    first = client.post(f"/review/{card['id']}", json={"rating": 3}).json()

    reset = client.post("/review/session/reset")
    assert reset.status_code == 204

    card = client.get("/review/next").json()
    second = client.post(f"/review/{card['id']}", json={"rating": 3}).json()

    assert first["session_id"] != second["session_id"]


@pytest.mark.skipif(not PYTHON_DECK.exists(), reason="PYTHON_DECK.md not available")
def test_import_real_python_deck(client: TestClient) -> None:
    response = client.post("/import", json={"path": str(PYTHON_DECK)})
    assert response.status_code == 200
    payload = response.json()
    assert payload["imported"] == 200
    assert payload["decks"] == 42

    stats = client.get("/stats").json()
    assert stats["total_cards"] == 200
    assert stats["due_today"] == 200
