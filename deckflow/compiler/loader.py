from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from deckflow.extract.card_file import parse_card_file
from deckflow.schemas.specs import CardSpec, CollectionSpec, DeckSpec, ProjectManifest, SchemaRules

CollectionLoadResult = tuple[
    Path, CollectionSpec, dict[str, DeckSpec], list[CardSpec], SchemaRules | None
]


def load_project_manifest(project_root: Path) -> ProjectManifest:
    manifest_path = project_root / "deckflow.yaml"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Project manifest not found: {manifest_path}")
    data = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    return ProjectManifest.model_validate(data)


def load_collection_spec(collection_dir: Path) -> CollectionSpec:
    spec_path = collection_dir / "collection.yaml"
    if not spec_path.exists():
        raise FileNotFoundError(f"Collection spec not found: {spec_path}")
    data = yaml.safe_load(spec_path.read_text(encoding="utf-8")) or {}
    return CollectionSpec.model_validate(data)


def load_schema_rules(collection_dir: Path) -> SchemaRules | None:
    schema_path = collection_dir / "schema.yaml"
    if not schema_path.exists():
        return None
    data = yaml.safe_load(schema_path.read_text(encoding="utf-8")) or {}
    return SchemaRules.model_validate(data)


def load_deck_specs(collection_dir: Path) -> dict[str, DeckSpec]:
    decks_dir = collection_dir / "decks"
    specs: dict[str, DeckSpec] = {}
    if not decks_dir.exists():
        return specs
    for deck_file in sorted(decks_dir.glob("*.yaml")):
        data = yaml.safe_load(deck_file.read_text(encoding="utf-8")) or {}
        deck = DeckSpec.model_validate(data)
        specs[deck.path] = deck
    return specs


def load_card_specs(collection_dir: Path) -> list[CardSpec]:
    cards_dir = collection_dir / "cards"
    if not cards_dir.exists():
        return []
    specs: list[CardSpec] = []
    for card_file in sorted(cards_dir.glob("*.md")):
        specs.append(parse_card_file(card_file))
    return specs


def load_collection(
    collection_dir: Path,
    project_defaults: dict[str, Any] | None = None,
) -> tuple[CollectionSpec, dict[str, DeckSpec], list[CardSpec], SchemaRules | None]:
    collection = load_collection_spec(collection_dir)
    decks = load_deck_specs(collection_dir)
    cards = load_card_specs(collection_dir)
    rules = load_schema_rules(collection_dir)

    if project_defaults:
        default_config = project_defaults.get("config", {})
        if default_config:
            merged = dict(default_config)
            merged.update(collection.config)
            collection.config = merged

    return collection, decks, cards, rules


def load_project(
    project_root: Path,
) -> list[CollectionLoadResult]:
    manifest = load_project_manifest(project_root)
    defaults = manifest.defaults
    results: list[CollectionLoadResult] = []

    for collection_path in manifest.collections:
        collection_dir = (project_root / collection_path).resolve()
        if not collection_dir.is_dir():
            raise FileNotFoundError(f"Collection directory not found: {collection_dir}")
        collection, decks, cards, rules = load_collection(collection_dir, defaults)
        results.append((collection_dir, collection, decks, cards, rules))

    return results
