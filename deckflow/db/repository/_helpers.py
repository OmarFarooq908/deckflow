from __future__ import annotations

import json
from typing import Any

from deckflow.models.domain import CardRow, ParsedCard


def json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_safe(v) for v in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def dump_json(data: dict[str, Any] | None) -> str:
    return json.dumps(json_safe(data or {}))


def card_meta(card: ParsedCard) -> dict[str, Any]:
    meta = dict(card.meta)
    meta.update(
        {
            "status": card.status,
            "links": card.links,
            "hint": card.hint,
            "notes": card.notes,
            "source": card.source,
            "priority": card.priority,
            "concepts": card.concepts,
            "prerequisites": card.prerequisites,
            "difficulty": card.difficulty,
            "objective": card.objective,
        }
    )
    return {k: v for k, v in meta.items() if v is not None}


def row_to_card(row: Any) -> CardRow:
    import sqlite3

    assert isinstance(row, sqlite3.Row)
    meta_raw = row["meta_json"] if "meta_json" in row else "{}"
    meta = json.loads(meta_raw) if meta_raw else {}
    return CardRow(
        id=int(row["id"]),
        deck_id=int(row["deck_id"]),
        front_md=row["front_md"],
        back_md=row["back_md"],
        card_type=row["card_type"],
        tags=json.loads(row["tags_json"]),
        source_line=int(row["source_line"]),
        card_index=int(row["card_index"]),
        deck_path=row["deck_path"],
        card_uid=row["card_uid"] if "card_uid" in row else None,
        hint=meta.get("hint"),
        links=meta.get("links") or [],
        status=meta.get("status") or "active",
        priority=meta.get("priority") or "normal",
    )
