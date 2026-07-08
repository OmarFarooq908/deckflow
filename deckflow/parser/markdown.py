from __future__ import annotations

from pathlib import Path

from deckflow.models.domain import ParsedCard, ParsedDeck
from deckflow.parser.legacy import parse_legacy_deck
from deckflow.parser.v1 import parse_v1_deck


def parse_markdown_deck(path: Path) -> list[ParsedCard]:
    """Parse a markdown deck file (v1 or legacy format)."""
    text = path.read_text(encoding="utf-8")
    parsed = parse_markdown_deck_text(text)
    return parsed.cards


def parse_markdown_deck_text(text: str) -> ParsedDeck:
    if text.startswith("---"):
        collection, decks, cards = parse_v1_deck(text)
        if collection is not None:
            return ParsedDeck(collection=collection, decks=decks, cards=cards)

    lines = text.splitlines()
    cards = parse_legacy_deck(lines)
    return ParsedDeck(collection=None, decks=[], cards=cards)
