from __future__ import annotations

from datetime import UTC, datetime

from deckflow.db.repository import Repository
from deckflow.models.domain import CardRow, QueueCard, ReviewFocus

PRIORITY_WEIGHTS = {"high": 1.0, "normal": 0.5, "low": 0.2}


def build_daily_queue(
    repo: Repository,
    limit: int = 20,
    now: datetime | None = None,
    focus: ReviewFocus | None = None,
) -> list[QueueCard]:
    now = now or datetime.now(UTC)
    config = repo.get_collection_config()
    new_per_day = int(config.get("new_per_day", 20))
    max_reviews = int(config.get("max_reviews_per_day", 150))
    limit = min(limit, max_reviews)
    review_order = str(config.get("review_order", "score"))

    deck_prefix = focus.deck_prefix if focus else None
    concept_slug = focus.concept_slug if focus else None

    candidates = repo.get_due_candidates_filtered(
        now=now,
        deck_prefix=deck_prefix,
        concept_slug=concept_slug,
    )
    new_today = repo.count_new_cards_today(now)
    new_budget_left = max(0, new_per_day - new_today)

    pool: list[CardRow] = []
    for card in candidates:
        scheduling = repo.get_scheduling(card.id)
        if scheduling is None:
            continue
        is_new = scheduling.reps == 0
        if is_new and new_budget_left <= 0:
            continue
        pool.append(card)

    result: list[QueueCard] = []
    recent_concepts: list[str] = []

    while pool and len(result) < limit:
        scored = [_score_card(card, repo, now, recent_concepts, focus) for card in pool]
        if review_order == "deck":
            best = min(
                scored,
                key=lambda item: (item.card.deck_path, item.card.card_index, -item.score),
            )
        else:
            best = max(scored, key=lambda item: item.score)

        result.append(best)
        pool = [card for card in pool if card.id != best.card.id]
        for slug in repo.get_card_concept_slugs(best.card.id)[:2]:
            recent_concepts.append(slug)

    return result


def resolve_track_focus(repo: Repository, track_id: str) -> ReviewFocus | None:
    from deckflow.service.library_service import get_track_focus

    return get_track_focus(repo, track_id)


def _score_card(
    card: CardRow,
    repo: Repository,
    now: datetime,
    recent_concepts: list[str],
    focus: ReviewFocus | None,
) -> QueueCard:
    scheduling = repo.get_scheduling(card.id)
    assert scheduling is not None

    is_new = scheduling.reps == 0
    due_urgency = _due_urgency(scheduling.due, now)
    weakness = repo.get_weakness_for_card(card.id)
    priority = _priority_weight(card)
    concept_penalty = _concept_fatigue(card.id, repo, recent_concepts)

    score = due_urgency * 3.0 + weakness * 2.0 + priority * 1.5 - concept_penalty * 1.0
    if is_new:
        score += 1.0

    reason = _build_reason(due_urgency, weakness, priority, is_new, card, repo)
    if focus and (focus.deck_prefix or focus.concept_slug):
        focus_label = focus.deck_prefix or focus.concept_slug or focus.track_id
        reason = f"focused: {focus_label}; {reason}"
    return QueueCard(card=card, score=score, reason=reason)


def _due_urgency(due: datetime, now: datetime) -> float:
    delta_hours = (now - due).total_seconds() / 3600
    if delta_hours >= 24:
        return 3.0
    if delta_hours >= 0:
        return 2.0
    return 1.0


def _priority_weight(card: CardRow) -> float:
    return PRIORITY_WEIGHTS.get(getattr(card, "priority", None) or "normal", 0.5)


def _concept_fatigue(card_id: int, repo: Repository, recent: list[str]) -> float:
    slugs = repo.get_card_concept_slugs(card_id)
    if not slugs:
        return 0.0
    overlap = sum(1 for slug in slugs if slug in recent[-3:])
    return float(overlap) * 0.5


def _build_reason(
    due_urgency: float,
    weakness: float,
    priority: float,
    is_new: bool,
    card: CardRow,
    repo: Repository,
) -> str:
    parts: list[str] = []
    if due_urgency >= 3.0:
        parts.append("overdue")
    elif due_urgency >= 2.0:
        parts.append("due now")
    if weakness >= 50:
        slugs = repo.get_card_concept_slugs(card.id)
        if slugs:
            parts.append(f"weak concept: {slugs[0]} ({weakness:.0f}% weakness)")
    if is_new:
        parts.append("new card")
    if priority >= 1.0:
        parts.append("high priority")
    return "; ".join(parts) if parts else "scheduled review"
