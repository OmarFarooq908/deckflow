from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from deckflow.config import get_db_path
from deckflow.db.repository import Repository
from deckflow.models.domain import ReviewTelemetry
from deckflow.service.analytics_service import (
    get_card_analytics,
    get_concepts,
    get_overview,
    get_study_plan,
    get_weak_spots,
)
from deckflow.service.import_service import import_deck
from deckflow.service.review_service import get_next_card, submit_review
from deckflow.service.stats_service import get_decks, get_last_import_path, get_stats

app = FastAPI(title="Deckflow API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_repo() -> Repository:
    repo = Repository(get_db_path())
    repo.initialize()
    return repo


class ImportRequest(BaseModel):
    path: str


class ImportResponse(BaseModel):
    imported: int
    decks: int
    path: str
    suspended: int = 0
    format: str = "legacy"
    collection_id: str | None = None


class CardResponse(BaseModel):
    id: int
    deck_path: str
    front_md: str
    back_md: str
    card_type: str | None = None
    tags: list[str] = Field(default_factory=list)
    hint: str | None = None
    links: list[str] = Field(default_factory=list)
    queue_reason: str | None = None


class ReviewRequest(BaseModel):
    rating: int = Field(ge=1, le=4)
    elapsed_ms: int | None = None
    reveal_ms: int | None = None
    rating_ms: int | None = None
    session_id: int | None = None


class ReviewSubmitResponse(BaseModel):
    card_id: int
    due: str
    reps: int


class StatsResponse(BaseModel):
    due_today: int
    new_cards: int
    reviewed_today: int
    total_cards: int
    retention_pct: float
    streak_days: int
    last_import_path: str | None = None


class DeckResponse(BaseModel):
    id: int
    path: str
    card_count: int
    due_count: int


class ConceptMasteryResponse(BaseModel):
    concept_id: int
    slug: str
    label: str
    card_count: int
    reviews_count: int
    retention_7d: float
    retention_30d: float
    mastery_score: float
    weakness_score: float


class WeakSpotResponse(BaseModel):
    concept_slug: str
    concept_label: str
    mastery_score: float
    retention_7d: float
    lapse_count: int
    message: str


class AnalyticsOverviewResponse(BaseModel):
    retention_7d: float
    retention_30d: float
    cards_per_day_7d: float
    avg_mastery: float
    streak_days: int
    due_today: int
    reviewed_today: int
    total_cards: int


class StudyPlanItemResponse(BaseModel):
    card_id: int
    card_uid: str | None = None
    deck_path: str
    front_preview: str
    reason: str
    score: float


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/import", response_model=ImportResponse)
def import_deck_endpoint(body: ImportRequest) -> ImportResponse:
    repo = get_repo()
    try:
        result = import_deck(repo, Path(body.path))
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ImportResponse(**result)


@app.get("/review/next", response_model=CardResponse | None)
def review_next() -> CardResponse | None:
    repo = get_repo()
    card, reason = get_next_card(repo)
    if card is None:
        return None
    return CardResponse(
        id=card.id,
        deck_path=card.deck_path,
        front_md=card.front_md,
        back_md=card.back_md,
        card_type=card.card_type,
        tags=card.tags,
        hint=card.hint,
        links=card.links,
        queue_reason=reason,
    )


@app.post("/review/{card_id}", response_model=ReviewSubmitResponse)
def review_submit(card_id: int, body: ReviewRequest) -> ReviewSubmitResponse:
    repo = get_repo()
    telemetry = ReviewTelemetry(
        reveal_ms=body.reveal_ms,
        rating_ms=body.rating_ms,
        session_id=body.session_id,
    )
    try:
        result = submit_review(
            repo,
            card_id,
            body.rating,
            telemetry=telemetry,
            elapsed_ms=body.elapsed_ms,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ReviewSubmitResponse(
        card_id=result.card.id,
        due=result.due.isoformat(),
        reps=result.reps,
    )


@app.get("/stats", response_model=StatsResponse)
def stats() -> StatsResponse:
    repo = get_repo()
    s = get_stats(repo)
    return StatsResponse(
        due_today=s.due_today,
        new_cards=s.new_cards,
        reviewed_today=s.reviewed_today,
        total_cards=s.total_cards,
        retention_pct=s.retention_pct,
        streak_days=s.streak_days,
        last_import_path=get_last_import_path(repo),
    )


@app.get("/decks", response_model=list[DeckResponse])
def decks() -> list[DeckResponse]:
    repo = get_repo()
    return [
        DeckResponse(
            id=d.id,
            path=d.path,
            card_count=d.card_count,
            due_count=d.due_count,
        )
        for d in get_decks(repo)
    ]


@app.get("/analytics/overview", response_model=AnalyticsOverviewResponse)
def analytics_overview() -> AnalyticsOverviewResponse:
    repo = get_repo()
    overview = get_overview(repo)
    return AnalyticsOverviewResponse(
        retention_7d=overview.retention_7d,
        retention_30d=overview.retention_30d,
        cards_per_day_7d=overview.cards_per_day_7d,
        avg_mastery=overview.avg_mastery,
        streak_days=overview.streak_days,
        due_today=overview.due_today,
        reviewed_today=overview.reviewed_today,
        total_cards=overview.total_cards,
    )


@app.get("/analytics/concepts", response_model=list[ConceptMasteryResponse])
def analytics_concepts() -> list[ConceptMasteryResponse]:
    repo = get_repo()
    return [
        ConceptMasteryResponse(
            concept_id=c.concept_id,
            slug=c.slug,
            label=c.label,
            card_count=c.card_count,
            reviews_count=c.reviews_count,
            retention_7d=c.retention_7d,
            retention_30d=c.retention_30d,
            mastery_score=c.mastery_score,
            weakness_score=c.weakness_score,
        )
        for c in get_concepts(repo)
    ]


@app.get("/analytics/weak-spots", response_model=list[WeakSpotResponse])
def analytics_weak_spots(limit: int = 10) -> list[WeakSpotResponse]:
    repo = get_repo()
    return [
        WeakSpotResponse(
            concept_slug=s.concept_slug,
            concept_label=s.concept_label,
            mastery_score=s.mastery_score,
            retention_7d=s.retention_7d,
            lapse_count=s.lapse_count,
            message=s.message,
        )
        for s in get_weak_spots(repo, limit=limit)
    ]


@app.get("/analytics/cards/{card_id}")
def analytics_card(card_id: int) -> dict[str, Any]:
    repo = get_repo()
    try:
        return get_card_analytics(repo, card_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/study-plan/today", response_model=list[StudyPlanItemResponse])
def study_plan_today(limit: int = 20) -> list[StudyPlanItemResponse]:
    repo = get_repo()
    return [
        StudyPlanItemResponse(
            card_id=item.card_id,
            card_uid=item.card_uid,
            deck_path=item.deck_path,
            front_preview=item.front_preview,
            reason=item.reason,
            score=item.score,
        )
        for item in get_study_plan(repo, limit=limit)
    ]
