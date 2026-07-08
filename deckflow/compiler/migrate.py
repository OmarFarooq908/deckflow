from __future__ import annotations

import textwrap
from pathlib import Path

import yaml

from deckflow.extract.markdown_v1 import compile_v1_markdown
from deckflow.schemas.compiled import CompiledCard, CompiledCollection, CompiledDeckMeta


def migrate_v1_to_project(source_md: Path, output_dir: Path) -> Path:
    """Convert a v1 monolithic markdown deck into a v2 project directory."""
    source_md = source_md.expanduser().resolve()
    output_dir = output_dir.expanduser().resolve()

    if not source_md.exists():
        raise FileNotFoundError(f"Source deck not found: {source_md}")

    text = source_md.read_text(encoding="utf-8")
    compiled = compile_v1_markdown(text, source_md)
    if compiled.collection is None:
        raise ValueError("Migration requires a v1 deck with collection frontmatter (deckflow: 1)")

    collection = compiled.collection
    project_name = collection.collection_id
    project_root = output_dir / project_name
    collection_dir = project_root / "collections" / collection.collection_id

    _write_project_manifest(project_root, collection.collection_id)
    _write_collection_yaml(collection_dir, compiled)
    _write_deck_yamls(collection_dir, compiled.decks)
    _write_card_files(collection_dir, compiled.cards)

    return project_root


def _write_project_manifest(project_root: Path, collection_id: str) -> None:
    project_root.mkdir(parents=True, exist_ok=True)
    manifest = {
        "deckflow": 2,
        "name": collection_id,
        "version": "1.0.0",
        "collections": [f"collections/{collection_id}"],
        "defaults": {"config": {}},
    }
    (project_root / "deckflow.yaml").write_text(
        yaml.safe_dump(manifest, sort_keys=False),
        encoding="utf-8",
    )


def _write_collection_yaml(collection_dir: Path, compiled: CompiledCollection) -> None:
    assert compiled.collection is not None
    c = compiled.collection
    payload: dict[str, object] = {
        "deckflow": 2,
        "id": c.collection_id,
        "title": c.title,
        "tags": c.tags,
        "config": c.config,
    }
    if c.description:
        payload["description"] = c.description
    payload.update(c.meta)
    collection_dir.mkdir(parents=True, exist_ok=True)
    (collection_dir / "collection.yaml").write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def _write_deck_yamls(collection_dir: Path, decks: list[CompiledDeckMeta]) -> None:
    decks_dir = collection_dir / "decks"
    decks_dir.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    for deck in decks:
        if deck.path in seen:
            continue
        seen.add(deck.path)
        slug = _deck_slug(deck.path)
        payload: dict[str, object] = {
            "path": deck.path,
            "tags": deck.tags,
            "config": {**deck.config, "inherit_tags": False},
        }
        if deck.description:
            payload["description"] = deck.description
        (decks_dir / f"{slug}.yaml").write_text(
            yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )


def _write_card_files(collection_dir: Path, cards: list[CompiledCard]) -> None:
    cards_dir = collection_dir / "cards"
    cards_dir.mkdir(parents=True, exist_ok=True)
    for card in cards:
        slug = card.meta.get("slug", card.card_uid)
        filename = f"{slug}.md" if isinstance(slug, str) else f"{card.card_uid}.md"
        frontmatter: dict[str, object] = {
            "id": card.card_uid,
            "deck": card.deck_path,
        }
        if card.card_type:
            frontmatter["type"] = card.card_type
        if card.concepts:
            frontmatter["concepts"] = card.concepts
        if card.tags:
            frontmatter["tags"] = card.tags
        if card.prerequisites:
            frontmatter["prerequisites"] = card.prerequisites
        if card.difficulty is not None:
            frontmatter["difficulty"] = card.difficulty
        if card.objective:
            frontmatter["objective"] = card.objective
        if card.priority:
            frontmatter["priority"] = card.priority
        if card.status != "active":
            frontmatter["status"] = card.status
        if card.links:
            frontmatter["links"] = card.links
        if card.hint:
            frontmatter["hint"] = card.hint
        if card.notes:
            frontmatter["notes"] = card.notes
        if card.source:
            frontmatter["source"] = card.source
        card_config = card.meta.get("card_config")
        if card_config:
            frontmatter["config"] = card_config

        yaml_block = yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True).strip()
        body = f"{card.front_md}\n\n---\n\n{card.back_md}\n"
        content = f"---\n{yaml_block}\n---\n\n{body}"
        (cards_dir / filename).write_text(content, encoding="utf-8")


def _deck_slug(deck_path: str) -> str:
    slug = deck_path.lower().replace("::", "-").replace(" ", "-").replace("&", "and")
    return "".join(ch if ch.isalnum() or ch == "-" else "-" for ch in slug).strip("-")


def scaffold_project(name: str, output_dir: Path) -> Path:
    """Create an empty v2 project template."""
    project_root = output_dir.expanduser().resolve() / name
    collection_id = name.replace("_", "-")
    collection_dir = project_root / "collections" / collection_id

    manifest = {
        "deckflow": 2,
        "name": name,
        "version": "1.0.0",
        "collections": [f"collections/{collection_id}"],
        "defaults": {
            "config": {
                "new_per_day": 20,
                "max_reviews_per_day": 150,
            }
        },
    }
    project_root.mkdir(parents=True, exist_ok=True)
    (project_root / "deckflow.yaml").write_text(
        yaml.safe_dump(manifest, sort_keys=False),
        encoding="utf-8",
    )

    collection = {
        "deckflow": 2,
        "id": collection_id,
        "title": name.replace("-", " ").title(),
        "tags": [],
        "config": {},
    }
    collection_dir.mkdir(parents=True, exist_ok=True)
    (collection_dir / "collection.yaml").write_text(
        yaml.safe_dump(collection, sort_keys=False),
        encoding="utf-8",
    )

    decks_dir = collection_dir / "decks"
    cards_dir = collection_dir / "cards"
    decks_dir.mkdir(exist_ok=True)
    cards_dir.mkdir(exist_ok=True)

    deck = {
        "path": "Default",
        "description": "Default deck",
        "tags": [],
        "config": {},
    }
    (decks_dir / "default.yaml").write_text(
        yaml.safe_dump(deck, sort_keys=False),
        encoding="utf-8",
    )

    sample_card = textwrap.dedent("""\
        ---
        id: sample-001
        deck: Default
        type: recognition
        tags: [sample]
        ---

        What is Deckflow?

        ---

        A data-centric spaced repetition tool for git-native learning decks.
        """)
    (cards_dir / "sample-001.md").write_text(sample_card, encoding="utf-8")

    return project_root
