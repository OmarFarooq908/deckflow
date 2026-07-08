from __future__ import annotations

from pathlib import Path

import pytest

from deckflow.compiler.compile import compile_path
from deckflow.compiler.migrate import migrate_v1_to_project
from deckflow.compiler.validator import ValidationError
from deckflow.extract.card_file import parse_card_file

V2_PROJECT = Path(__file__).parent.parent / "examples" / "python-de-interview"
V1_LEGACY = Path(__file__).parent.parent / "examples" / "legacy" / "advanced_sample_deck.md"


SAMPLE_CARD = """\
---
id: test-001
deck: Default
type: recognition
tags: [test]
---

What is 2 + 2?

---

4
"""


def test_parse_card_file_front_back() -> None:
    spec = parse_card_file(Path("test.md"), SAMPLE_CARD)
    assert spec.id == "test-001"
    assert "2 + 2" in spec.front_md
    assert spec.back_md.strip() == "4"


def test_parse_card_file_invalid_missing_separator() -> None:
    bad = "---\nid: x\ndeck: Default\n---\nonly front\n"
    with pytest.raises(ValueError, match="separator"):
        parse_card_file(Path("bad.md"), bad)


def test_compile_v2_project_card_count() -> None:
    compiled = compile_path(V2_PROJECT)
    assert len(compiled) == 1
    assert len(compiled[0].cards) == 12


def test_compile_v2_project_collection_meta() -> None:
    compiled = compile_path(V2_PROJECT)[0]
    assert compiled.collection is not None
    assert compiled.collection.collection_id == "python-de-interview"
    assert compiled.format == "v2"
    tracks = compiled.collection.meta.get("tracks", [])
    assert len(tracks) >= 1
    assert tracks[0]["id"] == "fundamentals-first"


def test_v2_tag_resolution() -> None:
    compiled = compile_path(V2_PROJECT)[0]
    card = next(c for c in compiled.cards if c.card_uid == "py-001")
    assert "python" in card.tags
    assert "immutable" in card.tags


def test_v2_prerequisite_validation() -> None:
    bad_card = """\
---
id: bad-001
deck: Default
prerequisites: [nonexistent-id]
---

Front?

---

Back.
"""
    from deckflow.compiler.resolver import resolve_collection
    from deckflow.schemas.specs import CollectionSpec

    collection = CollectionSpec(id="test", title="Test")
    card = parse_card_file(Path("bad.md"), bad_card)
    _, _, cards = resolve_collection(collection, {}, [card])
    with pytest.raises(ValidationError, match="prerequisite"):
        from deckflow.compiler.validator import validate_cards

        validate_cards(cards)


def test_migrate_round_trip_card_count(tmp_path: Path) -> None:
    project = migrate_v1_to_project(V1_LEGACY, tmp_path)
    compiled = compile_path(project)
    assert len(compiled[0].cards) == 12
    uids = {c.card_uid for c in compiled[0].cards}
    assert "py-001" in uids
    assert "lc-347" in uids


def test_v1_still_compiles_via_adapter() -> None:
    compiled = compile_path(V1_LEGACY)
    assert len(compiled[0].cards) == 12
    assert compiled[0].format == "v1"
