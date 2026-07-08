from __future__ import annotations

from datetime import UTC, datetime

from deckflow.db.repository import Repository
from deckflow.models.domain import CardRow, QueueCard

PRIORITY_WEIGHTS = {"high": 1.0, "normal": 0.5, "low": 0.2}


def build_daily_queue(
    repo: Repository,
    limit: int = 20,
    now: datetime | None = None,
) -> list[QueueCard]:
    now = now or datetime.now(UTC)
    config = repo.get_collection_config()
    new_per_day = int(config.get("new_per_day", 20))
    max_reviews = int(config.get("max_reviews_per_day", 150))
    limit = min(limit, max_reviews)

    candidates = repo.get_due_candidates(now=now)
    new_today = repo.count_new_cards_today(now)
    new_budget_left = max(0, new_per_day - new_today)

    scored: list[QueueCard] = []
    recent_concepts: list[str] = []

    for card in candidates:
        scheduling = repo.get_scheduling(card.id)
        if scheduling is None:
            continue

        is_new = scheduling.reps == 0
        if is_new and new_budget_left <= 0:
            continue

        due_urgency = _due_urgency(scheduling.due, now)
        weakness = repo.get_weakness_for_card(card.id)
        priority = _priority_weight(card)
        concept_penalty = _concept_fatigue(card.id, repo, recent_concepts)

        score = due_urgency * 3.0 + weakness * 2.0 + priority * 1.5 - concept_penalty * 1.0
        if is_new:
            score += 1.0

        reason = _build_reason(due_urgency, weakness, priority, is_new, card, repo)
        scored.append(QueueCard(card=card, score=score, reason=reason))

    scored.sort(key=lambda item: item.score, reverse=True)
    result = scored[:limit]

    for item in result:
        for slug in repo.get_card_concept_slugs(item.card.id)[:2]:
            recent_concepts.append(slug)

    return result


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
