from __future__ import annotations

from pathlib import Path

from deckflow.parser.markdown import parse_markdown_deck_text
from deckflow.schemas.compiled import (
    CompiledCard,
    CompiledCollection,
    CompiledCollectionMeta,
    CompiledDeckMeta,
)


def compile_v1_markdown(text: str, source_path: Path | None = None) -> CompiledCollection:
    """Adapt v1/legacy markdown parse output to CompiledCollection."""
    parsed = parse_markdown_deck_text(text)
    collection = None
    if parsed.collection:
        collection = CompiledCollectionMeta(
            collection_id=parsed.collection.collection_id,
            title=parsed.collection.title,
            description=parsed.collection.description,
            tags=list(parsed.collection.tags),
            config=dict(parsed.collection.config),
            meta=dict(parsed.collection.meta),
            deckflow_version=parsed.collection.deckflow_version,
        )

    decks = [
        CompiledDeckMeta(
            path=d.path,
            description=d.description,
            tags=list(d.tags),
            config=dict(d.config),
        )
        for d in parsed.decks
    ]

    cards = [
        CompiledCard(
            deck_path=c.deck_path,
            card_index=c.card_index,
            source_line=c.source_line,
            front_md=c.front_md,
            back_md=c.back_md,
            card_uid=c.card_uid or f"card-{c.card_index}",
            card_type=c.card_type,
            tags=list(c.tags),
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
            source_file=str(source_path) if source_path else None,
        )
        for c in parsed.cards
    ]

    fmt = "v1" if parsed.collection else "legacy"
    return CompiledCollection(
        collection=collection,
        decks=decks,
        cards=cards,
        source_root=source_path.parent if source_path else None,
        format=fmt,
    )
