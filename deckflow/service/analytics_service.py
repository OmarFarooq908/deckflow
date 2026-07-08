from __future__ import annotations

from typing import Any

from deckflow.db.repository import Repository
from deckflow.models.domain import (
    AnalyticsOverview,
    ConceptMastery,
    ReviewFocus,
    StudyPlanItem,
    WeakSpot,
)


def get_overview(repo: Repository) -> AnalyticsOverview:
    concepts = repo.list_concept_mastery()
    avg_mastery = sum(c.mastery_score for c in concepts) / len(concepts) if concepts else 0.0
    return AnalyticsOverview(
        retention_7d=repo.retention_for_days(7),
        retention_30d=repo.retention_for_days(30),
        cards_per_day_7d=repo.cards_per_day(7),
        avg_mastery=round(avg_mastery, 1),
        streak_days=repo.streak_days(),
        due_today=repo.count_due(),
        reviewed_today=repo.count_reviewed_today(),
        total_cards=repo.count_total_cards(),
    )


def get_concepts(repo: Repository) -> list[ConceptMastery]:
    return repo.list_concept_mastery()


def get_weak_spots(repo: Repository, limit: int = 10) -> list[WeakSpot]:
    concepts = repo.list_concept_mastery()
    spots: list[WeakSpot] = []
    for concept in concepts[:limit]:
        if concept.weakness_score < 30 and concept.mastery_score > 70:
            continue
        lapses = repo.count_lapses_for_concept(concept.slug, days=7)
        message = f"Review `{concept.slug}` — {concept.retention_7d:.0f}% retention (7d)"
        if lapses:
            message += f", {lapses} lapse(s) this week"
        spots.append(
            WeakSpot(
                concept_slug=concept.slug,
                concept_label=concept.label,
                mastery_score=concept.mastery_score,
                retention_7d=concept.retention_7d,
                lapse_count=lapses,
                message=message,
            )
        )
    return spots[:limit]


def get_study_plan(
    repo: Repository,
    limit: int = 20,
    focus: ReviewFocus | None = None,
) -> list[StudyPlanItem]:
    from deckflow.service.queue_service import build_daily_queue, resolve_track_focus

    if focus and focus.track_id and not focus.deck_prefix and not focus.concept_slug:
        focus = resolve_track_focus(repo, focus.track_id) or focus

    queue = build_daily_queue(repo, limit=limit, focus=focus)
    items: list[StudyPlanItem] = []
    for entry in queue:
        preview = entry.card.front_md.replace("\n", " ")[:80]
        items.append(
            StudyPlanItem(
                card_id=entry.card.id,
                card_uid=entry.card.card_uid,
                deck_path=entry.card.deck_path,
                front_preview=preview,
                reason=entry.reason,
                score=round(entry.score, 2),
            )
        )
    return items


def get_card_analytics(repo: Repository, card_id: int) -> dict[str, Any]:
    card = repo.get_card(card_id)
    if card is None:
        raise ValueError(f"Card not found: {card_id}")
    scheduling = repo.get_scheduling(card_id)
    history = repo.get_card_review_history(card_id)
    return {
        "card_id": card_id,
        "card_uid": card.card_uid,
        "deck_path": card.deck_path,
        "tags": card.tags,
        "concepts": repo.get_card_concept_slugs(card_id),
        "reps": scheduling.reps if scheduling else 0,
        "lapses": scheduling.lapses if scheduling else 0,
        "due": scheduling.due.isoformat() if scheduling else None,
        "reviews": history,
    }
