from __future__ import annotations

import random
from datetime import UTC, datetime
from typing import Any

from deckflow.db.repository import Repository
from deckflow.models.domain import CardRow, QueueCard, ReviewFocus

PRIORITY_WEIGHTS = {"high": 1.0, "normal": 0.5, "low": 0.2}


def _collection_config(
    repo: Repository,
    collection_id: int | None,
    cache: dict[int | None, dict[str, Any]],
) -> dict[str, Any]:
    if collection_id not in cache:
        if collection_id is None:
            config = repo.get_collection_config()
        else:
            config = repo.get_collection_config(collection_id)
        cache[collection_id] = config
    return cache[collection_id]


def _collection_reviews_left(
    repo: Repository,
    collection_id: int | None,
    now: datetime,
    cache: dict[int | None, int],
    config_cache: dict[int | None, dict[str, Any]],
) -> int:
    if collection_id not in cache:
        if collection_id is None:
            config = repo.get_collection_config()
        else:
            config = repo.get_collection_config(collection_id)
        max_reviews = int(config.get("max_reviews_per_day", 150))
        if collection_id is None:
            reviewed = repo.count_reviewed_today_for_orphan_decks(now)
        else:
            reviewed = repo.count_reviewed_today_for_collection(collection_id, now)
        cache[collection_id] = max(0, max_reviews - reviewed)
    return cache[collection_id]


def build_daily_queue(
    repo: Repository,
    limit: int = 20,
    now: datetime | None = None,
    focus: ReviewFocus | None = None,
) -> list[QueueCard]:
    now = now or datetime.now(UTC)
    collection_config_cache: dict[int | None, dict[str, Any]] = {}
    collection_reviews_left: dict[int | None, int] = {}

    total_reviews_left = sum(
        _collection_reviews_left(
            repo,
            collection_id,
            now,
            collection_reviews_left,
            collection_config_cache,
        )
        for collection_id in repo.get_active_collection_ids()
    )
    if total_reviews_left == 0:
        return []
    limit = min(limit, total_reviews_left)

    deck_prefix = focus.deck_prefix if focus else None
    concept_slug = focus.concept_slug if focus else None

    candidates = repo.get_due_candidates_filtered(
        now=now,
        deck_prefix=deck_prefix,
        concept_slug=concept_slug,
    )
    deck_new_remaining: dict[int, int] = {}
    deck_config_cache: dict[int, dict[str, Any]] = {}

    pool: list[CardRow] = []
    for card in candidates:
        scheduling = repo.get_scheduling(card.id)
        if scheduling is None:
            continue
        card_config = repo.get_scheduling_config_for_card(card.id)
        if repo.is_card_scheduling_blocked(card.id):
            continue
        is_new = scheduling.reps == 0
        if is_new:
            collection_id = repo.get_collection_id_for_deck(card.deck_id)
            coll_cfg = _collection_config(repo, collection_id, collection_config_cache)
            default_new_per_day = int(coll_cfg.get("new_per_day", 20))
            new_limit = int(card_config.get("new_per_day", default_new_per_day))
            if new_limit <= 0:
                continue
            deck_id = card.deck_id
            if deck_id not in deck_new_remaining:
                if deck_id not in deck_config_cache:
                    deck_config_cache[deck_id] = repo.get_scheduling_config_for_deck(deck_id)
                deck_limit = int(deck_config_cache[deck_id].get("new_per_day", default_new_per_day))
                used = repo.count_new_cards_today_for_deck(deck_id, now)
                deck_new_remaining[deck_id] = max(0, deck_limit - used)
            if deck_new_remaining[deck_id] <= 0:
                continue
        pool.append(card)

    result: list[QueueCard] = []
    recent_concepts: list[str] = []

    while pool and len(result) < limit:
        scored = [_score_card(card, repo, now, recent_concepts, focus) for card in pool]
        collection_ids = {repo.get_collection_id_for_deck(card.deck_id) for card in pool}
        if len(collection_ids) == 1:
            review_order = str(
                _collection_config(
                    repo,
                    next(iter(collection_ids)),
                    collection_config_cache,
                ).get("review_order", "score")
            )
        else:
            review_order = "score"
        if review_order == "deck":
            best = min(
                scored,
                key=lambda item: (item.card.deck_path, item.card.card_index, -item.score),
            )
        elif review_order == "random":
            best = random.choice(scored)
        else:
            best = max(scored, key=lambda item: item.score)

        collection_id = repo.get_collection_id_for_deck(best.card.deck_id)
        remaining_reviews = _collection_reviews_left(
            repo,
            collection_id,
            now,
            collection_reviews_left,
            collection_config_cache,
        )
        if remaining_reviews <= 0:
            pool = [card for card in pool if card.id != best.card.id]
            continue
        collection_reviews_left[collection_id] = remaining_reviews - 1

        scheduling = repo.get_scheduling(best.card.id)
        if scheduling is not None and scheduling.reps == 0:
            deck_id = best.card.deck_id
            remaining = deck_new_remaining.get(deck_id)
            if remaining is not None and remaining <= 0:
                pool = [card for card in pool if card.id != best.card.id]
                continue
            if remaining is not None:
                deck_new_remaining[deck_id] = remaining - 1

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
