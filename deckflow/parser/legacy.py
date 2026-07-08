from __future__ import annotations

import re

from deckflow.models.domain import ParsedCard

DECK_HEADER_RE = re.compile(r"^##\s+Deck:\s+(.+)$")
CARD_HEADER_RE = re.compile(r"^###\s+Card\s+(\d+)")
TAGS_RE = re.compile(r"^\*\*Tags:\*\*\s*(.*)$")
TYPE_RE = re.compile(r"^\*\*Type:\*\*\s*(.*)$")
FRONT_RE = re.compile(r"^\*\*Front:\*\*\s*$")
BACK_RE = re.compile(r"^\*\*Back:\*\*\s*$")
FIELD_STOP_RE = re.compile(r"^\*\*[^*]+:\*\*")


def parse_legacy_deck(lines: list[str]) -> list[ParsedCard]:
    current_deck = "Default"
    cards: list[ParsedCard] = []
    i = 0

    while i < len(lines):
        line = lines[i]
        deck_match = DECK_HEADER_RE.match(line.strip())
        if deck_match:
            current_deck = deck_match.group(1).strip()
            i += 1
            continue

        card_match = CARD_HEADER_RE.match(line.strip())
        if card_match:
            card_index = int(card_match.group(1))
            source_line = i + 1
            i += 1

            card_type = None
            tags: list[str] = []
            front_md = ""
            back_md = ""

            while i < len(lines):
                current = lines[i]
                stripped = current.strip()

                if CARD_HEADER_RE.match(stripped) or DECK_HEADER_RE.match(stripped):
                    break
                if stripped == "---":
                    i += 1
                    break

                tags_match = TAGS_RE.match(stripped)
                if tags_match:
                    tags = _parse_tags(tags_match.group(1))
                    i += 1
                    continue

                type_match = TYPE_RE.match(stripped)
                if type_match:
                    card_type = type_match.group(1).strip() or None
                    i += 1
                    continue

                if FRONT_RE.match(stripped):
                    i += 1
                    content, i = _read_content_block(lines, i)
                    front_md = content
                    continue

                if BACK_RE.match(stripped):
                    i += 1
                    content, i = _read_content_block(lines, i)
                    back_md = content
                    continue

                i += 1

            if front_md.strip() and back_md.strip():
                cards.append(
                    ParsedCard(
                        deck_path=current_deck,
                        card_index=card_index,
                        source_line=source_line,
                        front_md=front_md.strip(),
                        back_md=back_md.strip(),
                        card_type=card_type,
                        tags=tags,
                    )
                )
            continue

        i += 1

    return cards


def _parse_tags(raw: str) -> list[str]:
    tags = re.findall(r"`([^`]+)`", raw)
    if tags:
        return tags
    return [part.strip() for part in re.split(r"[,·]", raw) if part.strip()]


def _read_trailing_content(lines: list[str], start: int) -> tuple[str, int]:
    block_lines: list[str] = []
    i = start
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if (
            not stripped
            or stripped == "---"
            or CARD_HEADER_RE.match(stripped)
            or DECK_HEADER_RE.match(stripped)
            or TAGS_RE.match(stripped)
            or TYPE_RE.match(stripped)
            or FRONT_RE.match(stripped)
            or BACK_RE.match(stripped)
            or FIELD_STOP_RE.match(stripped)
        ):
            break
        block_lines.append(line)
        i += 1
    return "\n".join(block_lines), i


def _read_content_block(
    lines: list[str],
    start: int,
    stop_at_fields: bool = False,
) -> tuple[str, int]:
    if start >= len(lines):
        return "", start

    first = lines[start]
    stripped = first.strip()

    if stripped.startswith("```"):
        fence = stripped[:3]
        block_lines = [first]
        i = start + 1
        closed = False
        while i < len(lines):
            block_lines.append(lines[i])
            if lines[i].strip().startswith(fence) and i > start:
                closed = True
                i += 1
                break
            i += 1
        if closed:
            trailing, i = _read_trailing_content(lines, i)
            if trailing:
                block_lines.append(trailing)
        return "\n".join(block_lines), i

    if stripped.startswith(">"):
        block_lines = []
        i = start
        while i < len(lines):
            line = lines[i]
            if line.strip().startswith(">") or (not line.strip() and block_lines):
                block_lines.append(line)
                i += 1
                if not line.strip() and block_lines:
                    break
                continue
            if not line.strip():
                i += 1
                break
            break
        return "\n".join(block_lines), i

    block_lines = []
    i = start
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if (
            not stripped
            or stripped == "---"
            or CARD_HEADER_RE.match(stripped)
            or DECK_HEADER_RE.match(stripped)
            or TAGS_RE.match(stripped)
            or TYPE_RE.match(stripped)
            or FRONT_RE.match(stripped)
            or BACK_RE.match(stripped)
            or (stop_at_fields and FIELD_STOP_RE.match(stripped))
        ):
            break
        block_lines.append(line)
        i += 1
    return "\n".join(block_lines), i
