from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.main import app

FIXTURE = Path(__file__).parent / "fixtures" / "sample_deck.md"
PYTHON_DECK = Path(
    "/Users/dev/Documents/Personal/LeetCode/LeetCode/arb-data-engineer/anki/PYTHON_DECK.md"
)


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
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

    decks = client.get("/decks")
    assert decks.status_code == 200
    assert len(decks.json()) == 1


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
