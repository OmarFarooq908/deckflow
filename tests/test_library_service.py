from __future__ import annotations

from pathlib import Path

import pytest

from deckflow.db.repository import Repository
from deckflow.service.import_service import import_deck
from deckflow.service.library_service import (
    build_module_tree,
    build_topic_tree,
    build_track_summaries,
    get_learning_library,
    get_track_focus,
)

V2_PROJECT = Path(__file__).parent.parent / "examples" / "python-de-interview"
ADVANCED = Path(__file__).parent.parent / "examples" / "legacy" / "advanced_sample_deck.md"


@pytest.fixture()
def repo(tmp_path: Path) -> Repository:
    repository = Repository(tmp_path / "library.db")
    repository.initialize()
    return repository


def test_module_tree_rollup(repo: Repository) -> None:
    import_deck(repo, V2_PROJECT)
    modules = build_module_tree(repo)
    assert modules
    python = next(n for n in modules if n.label == "Python")
    assert python.card_count > 0
    assert python.due_count >= 0
    fundamentals = next(c for c in python.children if "Fundamentals" in c.label)
    assert fundamentals.card_count > 0
    assert fundamentals.children


def test_topic_tree_has_labels(repo: Repository) -> None:
    import_deck(repo, ADVANCED)
    topics = build_topic_tree(repo)
    assert topics
    slugs = {node.slug for node in _flatten_topics(topics)}
    assert "python::fundamentals" in slugs or any("python" in s for s in slugs)


def test_track_summaries_from_collection_meta(repo: Repository) -> None:
    import_deck(repo, V2_PROJECT)
    tracks = build_track_summaries(repo)
    assert len(tracks) >= 1
    track = next(t for t in tracks if t.id == "fundamentals-first")
    assert track.total_steps == 4
    assert track.title == "Fundamentals First"


def test_get_track_focus_resolves_current_step(repo: Repository) -> None:
    import_deck(repo, V2_PROJECT)
    focus = get_track_focus(repo, "fundamentals-first")
    assert focus is not None
    assert focus.deck_prefix or focus.concept_slug


def test_learning_library_payload(repo: Repository) -> None:
    import_deck(repo, V2_PROJECT)
    lib = get_learning_library(repo)
    assert lib.collection is not None
    assert lib.collection.slug == "python-de-interview"
    assert lib.modules
    assert lib.tracks


def _flatten_topics(nodes: list) -> list:
    result = []
    for node in nodes:
        result.append(node)
        result.extend(_flatten_topics(node.children))
    return result
