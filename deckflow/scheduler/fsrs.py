from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from fsrs import Card, Rating, Scheduler, State

DEFAULT_DESIRED_RETENTION = 0.9


def get_scheduler(desired_retention: float = DEFAULT_DESIRED_RETENTION) -> Scheduler:
    return Scheduler(desired_retention=desired_retention)


def new_fsrs_card(card_id: int) -> Card:
    return Card(card_id=card_id, due=datetime.now(UTC))


def card_from_json(fsrs_json: str) -> Card:
    return Card.from_dict(json.loads(fsrs_json))


def card_to_json(card: Card) -> str:
    return json.dumps(card.to_dict())


def get_retrievability(
    card: Card,
    at: datetime | None = None,
    desired_retention: float = DEFAULT_DESIRED_RETENTION,
) -> float:
    at = at or datetime.now(UTC)
    if at.tzinfo is None:
        at = at.replace(tzinfo=UTC)
    return float(get_scheduler(desired_retention).get_card_retrievability(card, at))


def fsrs_snapshot(card: Card) -> dict[str, Any]:
    return {
        "stability": card.stability,
        "difficulty": card.difficulty,
        "state": int(card.state) if isinstance(card.state, State) else card.state,
        "due": card.due.isoformat() if card.due else None,
        "reps": 1 if card.last_review else 0,
    }


def review_card(
    fsrs_json: str,
    rating: int,
    review_datetime: datetime | None = None,
    elapsed_ms: int | None = None,
    desired_retention: float = DEFAULT_DESIRED_RETENTION,
) -> tuple[Card, float]:
    card = card_from_json(fsrs_json)
    review_datetime = review_datetime or datetime.now(UTC)
    if review_datetime.tzinfo is None:
        review_datetime = review_datetime.replace(tzinfo=UTC)

    scheduler = get_scheduler(desired_retention)
    retrievability = float(scheduler.get_card_retrievability(card, review_datetime))
    updated, _log = scheduler.review_card(
        card,
        Rating(rating),
        review_datetime=review_datetime,
        review_duration=elapsed_ms,
    )
    return updated, retrievability
