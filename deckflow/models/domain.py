from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ParsedCollection:
    deckflow_version: int
    collection_id: str
    title: str
    description: str | None = None
    tags: list[str] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedDeckMeta:
    path: str
    description: str | None = None
    tags: list[str] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedCard:
    deck_path: str
    card_index: int
    source_line: int
    front_md: str
    back_md: str
    card_type: str | None = None
    tags: list[str] = field(default_factory=list)
    card_uid: str | None = None
    links: list[str] = field(default_factory=list)
    hint: str | None = None
    notes: str | None = None
    source: str | None = None
    priority: str | None = None
    status: str = "active"
    concepts: list[str] = field(default_factory=list)
    prerequisites: list[str] = field(default_factory=list)
    difficulty: int | None = None
    objective: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedDeck:
    collection: ParsedCollection | None
    decks: list[ParsedDeckMeta]
    cards: list[ParsedCard]


@dataclass
class DeckRow:
    id: int
    path: str
    source_file: str


@dataclass
class CardRow:
    id: int
    deck_id: int
    front_md: str
    back_md: str
    card_type: str | None
    tags: list[str]
    source_line: int
    card_index: int
    deck_path: str
    card_uid: str | None = None
    hint: str | None = None
    links: list[str] = field(default_factory=list)
    status: str = "active"
    priority: str = "normal"


@dataclass
class SchedulingRow:
    card_id: int
    due: datetime
    fsrs_json: str
    reps: int
    lapses: int


@dataclass
class ReviewResult:
    card: CardRow
    due: datetime
    reps: int


@dataclass
class Stats:
    due_today: int
    new_cards: int
    reviewed_today: int
    total_cards: int
    retention_pct: float
    streak_days: int


@dataclass
class DeckSummary:
    id: int
    path: str
    card_count: int
    due_count: int


@dataclass
class ReviewTelemetry:
    reveal_ms: int | None = None
    rating_ms: int | None = None
    session_id: int | None = None


@dataclass
class QueueCard:
    card: CardRow
    score: float
    reason: str


@dataclass
class ConceptMastery:
    concept_id: int
    slug: str
    label: str
    card_count: int
    reviews_count: int
    retention_7d: float
    retention_30d: float
    mastery_score: float
    weakness_score: float
    last_reviewed_at: datetime | None = None


@dataclass
class WeakSpot:
    concept_slug: str
    concept_label: str
    mastery_score: float
    retention_7d: float
    lapse_count: int
    message: str


@dataclass
class AnalyticsOverview:
    retention_7d: float
    retention_30d: float
    cards_per_day_7d: float
    avg_mastery: float
    streak_days: int
    due_today: int
    reviewed_today: int
    total_cards: int


@dataclass
class StudyPlanItem:
    card_id: int
    card_uid: str | None
    deck_path: str
    front_preview: str
    reason: str
    score: float
