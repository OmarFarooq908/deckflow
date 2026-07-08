from pathlib import Path

from deckflow.parser.markdown import parse_markdown_deck, parse_markdown_deck_text

ADVANCED = Path(__file__).parent.parent / "examples" / "legacy" / "advanced_sample_deck.md"
FIXTURE = Path(__file__).parent / "fixtures" / "sample_deck.md"


def test_v1_collection_frontmatter() -> None:
    parsed = parse_markdown_deck_text(ADVANCED.read_text(encoding="utf-8"))
    assert parsed.collection is not None
    assert parsed.collection.collection_id == "python-de-interview"
    assert parsed.collection.deckflow_version == 1
    assert "python" in parsed.collection.tags


def test_v1_card_count() -> None:
    cards = parse_markdown_deck(ADVANCED)
    assert len(cards) == 12


def test_v1_stable_card_uid() -> None:
    cards = parse_markdown_deck(ADVANCED)
    uids = {card.card_uid for card in cards}
    assert "py-001" in uids
    assert "lc-347" in uids
    assert len(uids) == len(cards)


def test_v1_tag_inheritance() -> None:
    cards = parse_markdown_deck(ADVANCED)
    card = next(c for c in cards if c.card_uid == "py-001")
    assert "python" in card.tags
    assert "fundamentals" in card.tags
    assert "immutable" in card.tags


def test_v1_suspended_cards_parsed() -> None:
    cards = parse_markdown_deck(ADVANCED)
    suspended = [c for c in cards if c.status == "suspended"]
    assert len(suspended) == 2
    assert any(c.card_uid == "lc-347-code" for c in suspended)


def test_v1_links_and_hint() -> None:
    cards = parse_markdown_deck(ADVANCED)
    card = next(c for c in cards if c.card_uid == "lc-347")
    assert "lc347" in card.links
    assert "file:" in card.links[1]

    hint_card = next(c for c in cards if c.card_uid == "py-003")
    assert hint_card.hint is not None


def test_v1_extra_appended_to_back() -> None:
    cards = parse_markdown_deck(ADVANCED)
    card = next(c for c in cards if c.card_uid == "pd-002")
    assert "join" in card.back_md.lower()
    assert "pd.merge" in card.back_md


def test_legacy_still_parses() -> None:
    cards = parse_markdown_deck(FIXTURE)
    assert len(cards) == 3
    assert cards[0].card_uid is None
