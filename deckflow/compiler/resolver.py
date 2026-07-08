from __future__ import annotations

from typing import Any

from deckflow.schemas.compiled import CompiledCard, CompiledCollectionMeta, CompiledDeckMeta
from deckflow.schemas.specs import CardSpec, CollectionSpec, DeckSpec


def merge_config(*layers: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for layer in layers:
        merged.update(layer)
    return merged


def merge_tags(
    collection_tags: list[str],
    deck_tags: list[str],
    card_tags: list[str],
    deck_config: dict[str, Any],
) -> list[str]:
    inherit = deck_config.get("inherit_tags", True)
    ordered: list[str] = []
    for group in (collection_tags, deck_tags if inherit else [], card_tags):
        for tag in group:
            if tag not in ordered:
                ordered.append(tag)
    return ordered


def resolve_collection(
    collection: CollectionSpec,
    decks: dict[str, DeckSpec],
    cards: list[CardSpec],
    project_config: dict[str, Any] | None = None,
) -> tuple[CompiledCollectionMeta, list[CompiledDeckMeta], list[CompiledCard]]:
    project_config = project_config or {}
    collection_meta = CompiledCollectionMeta(
        collection_id=collection.id,
        title=collection.title,
        description=collection.description,
        tags=list(collection.tags),
        config=merge_config(project_config, collection.config),
        meta={
            **collection.meta,
            "tracks": [t.model_dump() for t in collection.tracks],
        },
    )

    deck_meta_by_path: dict[str, CompiledDeckMeta] = {}
    for deck_path, deck in decks.items():
        deck_meta_by_path[deck_path] = CompiledDeckMeta(
            path=deck.path,
            description=deck.description,
            tags=list(deck.tags),
            config=merge_config(collection_meta.config, deck.config),
        )

    compiled_cards: list[CompiledCard] = []
    for index, card in enumerate(cards, start=1):
        deck_path = card.deck
        deck_spec = decks.get(deck_path)
        deck_tags = list(deck_spec.tags) if deck_spec else []
        deck_config = merge_config(
            collection_meta.config,
            deck_spec.config if deck_spec else {},
        )

        if deck_path not in deck_meta_by_path:
            deck_meta_by_path[deck_path] = CompiledDeckMeta(
                path=deck_path,
                description=None,
                tags=deck_tags,
                config=deck_config,
            )

        deck_meta = deck_meta_by_path[deck_path]
        merged_tags = merge_tags(
            collection_meta.tags,
            deck_meta.tags,
            card.tags,
            deck_meta.config,
        )
        card_config = merge_config(deck_meta.config, card.config)

        compiled_cards.append(
            CompiledCard(
                deck_path=deck_path,
                card_index=_stable_card_index(card.id, index),
                source_line=card.source_line,
                front_md=card.front_md,
                back_md=card.back_md,
                card_uid=card.id,
                card_type=card.type,
                tags=merged_tags,
                links=list(card.links),
                hint=card.hint,
                notes=card.notes,
                source=card.source,
                priority=card.priority,
                status=card.status,
                concepts=list(card.concepts),
                prerequisites=list(card.prerequisites),
                difficulty=card.difficulty,
                objective=card.objective,
                meta={
                    "card_config": card_config,
                    "deck_description": deck_meta.description,
                },
                source_file=card.source_file,
            )
        )

    return collection_meta, list(deck_meta_by_path.values()), compiled_cards


def _stable_card_index(card_uid: str, fallback: int) -> int:
    hashed = abs(hash(card_uid)) % 1_000_000
    return hashed if hashed else fallback
