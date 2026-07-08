from __future__ import annotations

import re
from typing import Any

import yaml

DECK_HEADER_V1_RE = re.compile(r"^##\s+Deck:\s+(.+)$")
CARD_HEADER_V1_RE = re.compile(r"^###\s+Card:\s+([a-z0-9][a-z0-9-]*)$", re.IGNORECASE)
CARD_HEADER_LEGACY_RE = re.compile(r"^###\s+Card\s+(\d+)")

FIELD_RE = re.compile(r"^\*\*(?P<key>[^*]+):\*\*\s*(?P<value>.*)$")
YAML_FENCE_RE = re.compile(r"^```ya?ml\s*$", re.IGNORECASE)


def parse_v1_deck(text: str) -> tuple[Any, list[Any], list[Any]]:
    collection, body = _parse_frontmatter(text)
    lines = body.splitlines()

    collection_tags = list(collection.tags) if collection else []
    collection_config = dict(collection.config) if collection else {}

    decks: list[Any] = []
    cards: list[Any] = []
    current_deck_path = "Default"
    current_deck_meta: dict[str, Any] = {}
    deck_tags: list[str] = []
    deck_config: dict[str, Any] = {}
    card_index_counter = 1

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        deck_match = DECK_HEADER_V1_RE.match(stripped)
        if deck_match:
            current_deck_path = deck_match.group(1).strip()
            current_deck_meta = {"path": current_deck_path}
            deck_tags = []
            deck_config = {}
            i += 1
            i = _consume_deck_metadata(lines, i, current_deck_meta, deck_tags, deck_config)
            from deckflow.models.domain import ParsedDeckMeta

            decks.append(
                ParsedDeckMeta(
                    path=current_deck_path,
                    description=current_deck_meta.get("description"),
                    tags=deck_tags,
                    config={**collection_config, **deck_config},
                )
            )
            continue

        card_match = CARD_HEADER_V1_RE.match(stripped)
        if card_match:
            slug = card_match.group(1).lower()
            source_line = i + 1
            i += 1

            card_fields, i = _parse_card_fields(lines, i)
            card_uid = card_fields.get("card_id") or slug
            card_type = card_fields.get("type")
            card_tags = _parse_tag_list(card_fields.get("tags", ""))
            priority = card_fields.get("priority")
            status = (card_fields.get("status") or "active").lower()
            links = _parse_links(card_fields.get("links", ""))
            hint = card_fields.get("hint")
            notes = card_fields.get("notes")
            source = card_fields.get("source")
            concepts = _parse_tag_list(card_fields.get("concepts", ""))
            prerequisites = _parse_tag_list(card_fields.get("prerequisites", ""))
            difficulty_raw = card_fields.get("difficulty")
            difficulty = (
                int(difficulty_raw) if difficulty_raw and str(difficulty_raw).isdigit() else None
            )
            objective = card_fields.get("objective")
            card_config = card_fields.get("card_config", {})

            front_md = card_fields.get("front", "")
            back_md = card_fields.get("back", "")
            extra = card_fields.get("extra", "")
            if extra:
                back_md = f"{back_md}\n\n{extra}".strip()

            merged_tags = _merge_tags(collection_tags, deck_tags, card_tags, deck_config)
            numeric_index = _stable_card_index(card_uid, card_index_counter)
            card_index_counter += 1

            if front_md.strip() and back_md.strip():
                from deckflow.models.domain import ParsedCard

                cards.append(
                    ParsedCard(
                        deck_path=current_deck_path,
                        card_index=numeric_index,
                        card_uid=card_uid,
                        source_line=source_line,
                        front_md=front_md.strip(),
                        back_md=back_md.strip(),
                        card_type=card_type,
                        tags=merged_tags,
                        links=links,
                        hint=hint,
                        notes=notes,
                        source=source,
                        concepts=concepts,
                        prerequisites=prerequisites,
                        difficulty=difficulty,
                        objective=objective,
                        priority=priority,
                        status=status,
                        meta={
                            "slug": slug,
                            "card_config": card_config,
                            "deck_description": current_deck_meta.get("description"),
                        },
                    )
                )
            continue

        i += 1

    return collection, decks, cards


def _parse_frontmatter(text: str) -> tuple[Any, str]:
    if not text.startswith("---"):
        return None, text

    end = text.find("\n---", 3)
    if end == -1:
        return None, text

    raw_yaml = text[3:end].strip()
    body = text[end + 4 :].lstrip("\n")
    data = yaml.safe_load(raw_yaml) or {}

    if data.get("deckflow") != 1:
        return None, text

    from deckflow.models.domain import ParsedCollection

    collection = ParsedCollection(
        deckflow_version=1,
        collection_id=str(data["id"]),
        title=str(data.get("title", data["id"])),
        description=data.get("description"),
        tags=list(data.get("tags") or []),
        config=dict(data.get("config") or {}),
        meta={
            k: v
            for k, v in data.items()
            if k
            not in {
                "deckflow",
                "id",
                "title",
                "description",
                "tags",
                "config",
            }
        },
    )
    return collection, body


def _consume_deck_metadata(
    lines: list[str],
    start: int,
    deck_meta: dict[str, Any],
    deck_tags: list[str],
    deck_config: dict[str, Any],
) -> int:
    i = start
    while i < len(lines):
        stripped = lines[i].strip()
        if (
            DECK_HEADER_V1_RE.match(stripped)
            or CARD_HEADER_V1_RE.match(stripped)
            or CARD_HEADER_LEGACY_RE.match(stripped)
        ):
            break

        if not stripped:
            i += 1
            continue

        field = FIELD_RE.match(stripped)
        if not field:
            i += 1
            continue

        key = field.group("key").strip().lower()
        value = field.group("value").strip()

        if key == "deck description":
            deck_meta["description"] = value
            i += 1
        elif key == "deck tags":
            deck_tags.extend(_parse_tag_list(value))
            i += 1
        elif key == "deck config":
            i += 1
            config_yaml, i = _read_yaml_fence(lines, i)
            if config_yaml:
                deck_config.update(yaml.safe_load(config_yaml) or {})
        else:
            i += 1

    return i


def _parse_card_fields(lines: list[str], start: int) -> tuple[dict[str, Any], int]:
    fields: dict[str, Any] = {}
    i = start

    while i < len(lines):
        stripped = lines[i].strip()

        if (
            stripped == "---"
            or DECK_HEADER_V1_RE.match(stripped)
            or CARD_HEADER_V1_RE.match(stripped)
            or CARD_HEADER_LEGACY_RE.match(stripped)
        ):
            if stripped == "---":
                i += 1
            break

        field = FIELD_RE.match(stripped)
        if field:
            key = _normalize_field_key(field.group("key"))
            value = field.group("value").strip()

            if key in {"deck config", "card config"}:
                i += 1
                config_yaml, i = _read_yaml_fence(lines, i)
                fields[key.replace(" ", "_")] = yaml.safe_load(config_yaml) or {}
                continue

            if key == "front":
                i += 1
                content, i = _read_content_until_field(lines, i)
                fields["front"] = content
                continue

            if key == "back":
                i += 1
                content, i = _read_content_until_field(lines, i)
                fields["back"] = content
                continue

            if key == "extra":
                i += 1
                content, i = _read_content_until_field(lines, i)
                fields["extra"] = content
                continue

            if key == "card id":
                fields["card_id"] = value.strip("` ")
            elif key == "type":
                fields["type"] = value
            elif key == "tags":
                fields["tags"] = value
            elif key == "priority":
                fields["priority"] = value.lower()
            elif key == "status":
                fields["status"] = value.lower()
            elif key == "links":
                fields["links"] = value
            elif key == "hint":
                fields["hint"] = value
            elif key == "notes":
                fields["notes"] = value
            elif key == "source":
                fields["source"] = value
            elif key == "concepts":
                fields["concepts"] = value
            elif key == "prerequisites":
                fields["prerequisites"] = value
            elif key == "difficulty":
                fields["difficulty"] = value.strip("` ")
            elif key == "objective":
                fields["objective"] = value
            else:
                fields[key.replace(" ", "_")] = value
            i += 1
            continue

        i += 1

    return fields, i


def _read_yaml_fence(lines: list[str], start: int) -> tuple[str, int]:
    if start >= len(lines) or not YAML_FENCE_RE.match(lines[start].strip()):
        return "", start

    block: list[str] = []
    i = start + 1
    while i < len(lines):
        if lines[i].strip() == "```":
            return "\n".join(block), i + 1
        block.append(lines[i])
        i += 1
    return "\n".join(block), i


def _read_content_until_field(lines: list[str], start: int) -> tuple[str, int]:
    from deckflow.parser.legacy import _read_content_block

    return _read_content_block(lines, start, stop_at_fields=True)


def _normalize_field_key(key: str) -> str:
    return key.strip().lower()


def _parse_tag_list(raw: str) -> list[str]:
    tags = re.findall(r"`([^`]+)`", raw)
    if tags:
        return tags
    return [part.strip() for part in re.split(r"[,·]", raw) if part.strip()]


def _parse_links(raw: str) -> list[str]:
    return re.findall(r"`([^`]+)`", raw) or [part.strip() for part in raw.split() if part.strip()]


def _merge_tags(
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


def _stable_card_index(card_uid: str, fallback: int) -> int:
    hashed = abs(hash(card_uid)) % 1_000_000
    return hashed if hashed else fallback
