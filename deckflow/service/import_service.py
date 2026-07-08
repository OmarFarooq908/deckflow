from __future__ import annotations

from pathlib import Path
from typing import Any

from deckflow.db.repository import Repository
from deckflow.parser.markdown import parse_markdown_deck_text


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def import_deck(repo: Repository, deck_path: Path) -> dict[str, Any]:
    deck_path = deck_path.expanduser().resolve()
    if not deck_path.exists():
        raise FileNotFoundError(f"Deck file not found: {deck_path}")

    parsed = parse_markdown_deck_text(deck_path.read_text(encoding="utf-8"))
    if not parsed.cards:
        raise ValueError(f"No cards found in {deck_path}")

    source_file = str(deck_path)
    collection_id: int | None = None

    if parsed.collection:
        collection_id = repo.upsert_collection(
            slug=parsed.collection.collection_id,
            title=parsed.collection.title,
            source_file=source_file,
            description=parsed.collection.description,
            config=_json_safe(parsed.collection.config),
            meta=_json_safe(parsed.collection.meta),
        )

    deck_ids: dict[str, int] = {}
    deck_meta_by_path = {deck.path: deck for deck in parsed.decks}
    imported = 0
    suspended = 0

    collection_meta = {}
    if parsed.collection:
        collection_meta = _json_safe(
            {
                "collection_id": parsed.collection.collection_id,
                "title": parsed.collection.title,
                "description": parsed.collection.description,
                "tags": parsed.collection.tags,
                "config": parsed.collection.config,
                **parsed.collection.meta,
            }
        )

    for card in parsed.cards:
        if card.deck_path not in deck_ids:
            deck_meta = deck_meta_by_path.get(card.deck_path)
            deck_meta_payload = _json_safe(
                {
                    "description": deck_meta.description if deck_meta else None,
                    "tags": deck_meta.tags if deck_meta else [],
                    "config": deck_meta.config if deck_meta else {},
                    "collection": collection_meta,
                }
            )
            deck_ids[card.deck_path] = repo.upsert_deck(
                card.deck_path,
                source_file,
                meta=deck_meta_payload,
                collection_id=collection_id,
            )
        repo.upsert_card(deck_ids[card.deck_path], card)
        imported += 1
        if card.status == "suspended":
            suspended += 1

    for deck_meta in parsed.decks:
        for tag in deck_meta.tags:
            repo.upsert_concept(tag)

    if parsed.collection:
        for tag in parsed.collection.tags:
            repo.upsert_concept(tag)

    return {
        "imported": imported,
        "decks": len(deck_ids),
        "suspended": suspended,
        "path": source_file,
        "format": "v1" if parsed.collection else "legacy",
        "collection_id": parsed.collection.collection_id if parsed.collection else None,
    }
