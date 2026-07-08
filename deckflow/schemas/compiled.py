from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from deckflow.models.domain import ParsedCard, ParsedCollection, ParsedDeck, ParsedDeckMeta


@dataclass
class CompiledCollectionMeta:
    collection_id: str
    title: str
    description: str | None = None
    tags: list[str] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=dict)
    deckflow_version: int = 2


@dataclass
class CompiledDeckMeta:
    path: str
    description: str | None = None
    tags: list[str] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class CompiledCard:
    deck_path: str
    card_index: int
    source_line: int
    front_md: str
    back_md: str
    card_uid: str
    card_type: str | None = None
    tags: list[str] = field(default_factory=list)
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
    source_file: str | None = None


@dataclass
class CompiledCollection:
    collection: CompiledCollectionMeta | None
    decks: list[CompiledDeckMeta]
    cards: list[CompiledCard]
    source_root: Path | None = None
    format: str = "v2"

    def to_parsed_deck(self) -> ParsedDeck:
        parsed_collection = None
        if self.collection:
            parsed_collection = ParsedCollection(
                deckflow_version=self.collection.deckflow_version,
                collection_id=self.collection.collection_id,
                title=self.collection.title,
                description=self.collection.description,
                tags=list(self.collection.tags),
                config=dict(self.collection.config),
                meta=dict(self.collection.meta),
            )
        return ParsedDeck(
            collection=parsed_collection,
            decks=[
                ParsedDeckMeta(
                    path=d.path,
                    description=d.description,
                    tags=list(d.tags),
                    config=dict(d.config),
                )
                for d in self.decks
            ],
            cards=[
                ParsedCard(
                    deck_path=c.deck_path,
                    card_index=c.card_index,
                    source_line=c.source_line,
                    front_md=c.front_md,
                    back_md=c.back_md,
                    card_type=c.card_type,
                    tags=list(c.tags),
                    card_uid=c.card_uid,
                    links=list(c.links),
                    hint=c.hint,
                    notes=c.notes,
                    source=c.source,
                    priority=c.priority,
                    status=c.status,
                    concepts=list(c.concepts),
                    prerequisites=list(c.prerequisites),
                    difficulty=c.difficulty,
                    objective=c.objective,
                    meta=dict(c.meta),
                )
                for c in self.cards
            ],
        )
