from __future__ import annotations

from pathlib import Path
from typing import Any

from deckflow.compiler.compile import compile_path
from deckflow.db.repository import Repository
from deckflow.schemas.compiled import CompiledCollection


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def import_compiled(repo: Repository, compiled: CompiledCollection) -> dict[str, Any]:
    if not compiled.cards:
        raise ValueError("No cards in compiled collection")

    parsed = compiled.to_parsed_deck()
    source_file = str(compiled.source_root) if compiled.source_root else "compiled"

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
        "format": compiled.format,
        "collection_id": parsed.collection.collection_id if parsed.collection else None,
    }


def import_deck(repo: Repository, deck_path: Path) -> dict[str, Any]:
    deck_path = deck_path.expanduser().resolve()
    if not deck_path.exists():
        raise FileNotFoundError(f"Deck path not found: {deck_path}")

    compiled_list = compile_path(deck_path)
    if not compiled_list:
        raise ValueError(f"No collections compiled from {deck_path}")

    totals: dict[str, Any] = {
        "imported": 0,
        "decks": 0,
        "suspended": 0,
        "path": str(deck_path),
        "format": compiled_list[0].format,
        "collection_id": None,
    }
    all_deck_paths: set[str] = set()

    for compiled in compiled_list:
        result = import_compiled(repo, compiled)
        totals["imported"] += result["imported"]
        totals["suspended"] += result["suspended"]
        totals["format"] = result["format"]
        if result.get("collection_id"):
            totals["collection_id"] = result["collection_id"]
        all_deck_paths.update(c.deck_path for c in compiled.cards)

    totals["decks"] = len(all_deck_paths)
    return totals
