from pathlib import Path

from deckflow.parser.markdown import parse_markdown_deck

FIXTURE = Path(__file__).parent / "fixtures" / "sample_deck.md"


def test_parse_sample_deck_card_count() -> None:
    cards = parse_markdown_deck(FIXTURE)
    assert len(cards) == 3


def test_parse_deck_paths() -> None:
    cards = parse_markdown_deck(FIXTURE)
    assert all(card.deck_path == "Sample::Basics" for card in cards)


def test_parse_tags_and_type() -> None:
    cards = parse_markdown_deck(FIXTURE)
    assert cards[0].tags == ["syntax", "recognition"]
    assert cards[0].card_type == "Recognition"
    assert "2 + 2" in cards[0].front_md
    assert "4" in cards[0].back_md


def test_parse_code_blocks() -> None:
    cards = parse_markdown_deck(FIXTURE)
    assert "```python" in cards[1].front_md
    assert "<class 'list'>" in cards[1].back_md
