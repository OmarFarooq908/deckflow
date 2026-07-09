from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from deckflow.db.repository import Repository
from deckflow.local_time import local_day_start
from deckflow.models.domain import (
    CardRow,
    QueueCard,
    ReviewFocus,
    ReviewResult,
    ReviewTelemetry,
)
from deckflow.scheduler.fsrs import (
    DEFAULT_DESIRED_RETENTION,
    card_from_json,
    card_to_json,
    fsrs_snapshot,
    review_card,
)
from deckflow.service.queue_service import build_daily_queue, resolve_track_focus


def get_next_card(
    repo: Repository,
    focus: ReviewFocus | None = None,
    exclude_card_ids: set[int] | None = None,
    queue_limit: int = 50,
) -> tuple[CardRow | None, str | None]:
    if focus and focus.track_id and not focus.deck_prefix and not focus.concept_slug:
        focus = resolve_track_focus(repo, focus.track_id) or focus
    queue = build_daily_queue(repo, limit=queue_limit, focus=focus)
    if not queue:
        return None, None
    excluded = exclude_card_ids or set()
    for item in queue:
        if item.card.id not in excluded:
            return item.card, item.reason
    return None, None


def submit_review(
    repo: Repository,
    card_id: int,
    rating: int,
    telemetry: ReviewTelemetry | None = None,
    elapsed_ms: int | None = None,
) -> ReviewResult:
    if rating not in (1, 2, 3, 4):
        raise ValueError("Rating must be between 1 and 4")

    card = repo.get_card(card_id)
    if card is None:
        raise ValueError(f"Card not found: {card_id}")

    scheduling = repo.get_scheduling(card_id)
    if scheduling is None:
        raise ValueError(f"Scheduling not found for card: {card_id}")

    telemetry = telemetry or ReviewTelemetry()
    reviewed_at = datetime.now(UTC)
    pre_card = card_from_json(scheduling.fsrs_json)
    snapshot = fsrs_snapshot(pre_card)
    card_config = repo.get_scheduling_config_for_card(card_id)
    desired_retention = float(card_config.get("desired_retention", DEFAULT_DESIRED_RETENTION))

    updated, retrievability = review_card(
        scheduling.fsrs_json,
        rating,
        review_datetime=reviewed_at,
        elapsed_ms=elapsed_ms or telemetry.rating_ms,
        desired_retention=desired_retention,
    )

    reps = scheduling.reps + 1
    lapses = scheduling.lapses + (1 if rating == 1 else 0)

    repo.update_scheduling(
        card_id=card_id,
        due=updated.due,
        fsrs_json=card_to_json(updated),
        reps=reps,
        lapses=lapses,
    )

    session_id = telemetry.session_id
    if session_id is None:
        session_id = repo.get_or_create_session()

    repo.record_review(
        card_id=card_id,
        rating=rating,
        reviewed_at=reviewed_at,
        elapsed_ms=elapsed_ms,
        reveal_ms=telemetry.reveal_ms,
        rating_ms=telemetry.rating_ms,
        retrievability=retrievability,
        stability=snapshot.get("stability"),
        difficulty=snapshot.get("difficulty"),
        state=snapshot.get("state"),
        fsrs_snapshot_json=json.dumps(snapshot),
        session_id=session_id,
    )
    repo.refresh_mastery_for_card(card_id)
    _bury_related_cards(repo, card_id, reviewed_at)

    return ReviewResult(card=card, due=updated.due, reps=reps, session_id=session_id)


def _bury_related_cards(repo: Repository, card_id: int, now: datetime) -> None:
    config = repo.get_scheduling_config_for_card(card_id)
    if not config.get("bury_related"):
        return
    related = config.get("related") or []
    if not related:
        return

    related_ids: list[int] = []
    for reference in related:
        related_ids.extend(repo.find_card_ids_by_reference(str(reference)))
    if not related_ids:
        return

    bury_until = local_day_start(now) + timedelta(days=1)
    repo.bury_cards_until(sorted(set(related_ids)), bury_until)


def get_queue(
    repo: Repository,
    limit: int = 20,
    focus: ReviewFocus | None = None,
) -> list[QueueCard]:
    if focus and focus.track_id and not focus.deck_prefix and not focus.concept_slug:
        focus = resolve_track_focus(repo, focus.track_id) or focus
    return build_daily_queue(repo, limit=limit, focus=focus)
