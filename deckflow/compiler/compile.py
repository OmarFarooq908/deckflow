from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path

from deckflow.compiler.loader import load_collection, load_project
from deckflow.compiler.resolver import resolve_collection
from deckflow.compiler.validator import validate_cards
from deckflow.extract.markdown_v1 import compile_v1_markdown
from deckflow.schemas.compiled import CompiledCollection


class SourceKind(StrEnum):
    PROJECT = "project"
    COLLECTION = "collection"
    MARKDOWN_V1 = "markdown_v1"
    MARKDOWN_LEGACY = "markdown_legacy"


def detect_source(path: Path) -> SourceKind:
    path = path.expanduser().resolve()
    if path.is_file():
        if path.suffix.lower() in {".md", ".markdown"}:
            text = path.read_text(encoding="utf-8")
            if text.startswith("---"):
                data_end = text.find("\n---", 3)
                if data_end != -1:
                    import yaml

                    data = yaml.safe_load(text[3:data_end].strip()) or {}
                    if data.get("deckflow") == 1:
                        return SourceKind.MARKDOWN_V1
            return SourceKind.MARKDOWN_LEGACY
        raise ValueError(f"Unsupported file type: {path}")

    if (path / "deckflow.yaml").exists():
        return SourceKind.PROJECT
    if (path / "collection.yaml").exists():
        return SourceKind.COLLECTION
    raise ValueError(f"Cannot detect deck source type: {path}")


def compile_path(path: Path) -> list[CompiledCollection]:
    kind = detect_source(path)
    if kind == SourceKind.PROJECT:
        return compile_project(path)
    if kind == SourceKind.COLLECTION:
        return [compile_collection_dir(path)]
    if kind in (SourceKind.MARKDOWN_V1, SourceKind.MARKDOWN_LEGACY):
        text = path.read_text(encoding="utf-8")
        return [compile_v1_markdown(text, path)]
    raise ValueError(f"Unsupported source kind: {kind}")


def compile_project(project_root: Path) -> list[CompiledCollection]:
    project_root = project_root.expanduser().resolve()
    loaded = load_project(project_root)
    results: list[CompiledCollection] = []

    for collection_dir, collection, decks, cards, rules in loaded:
        collection_meta, deck_metas, compiled_cards = resolve_collection(
            collection,
            decks,
            cards,
        )
        validate_cards(compiled_cards, rules)
        results.append(
            CompiledCollection(
                collection=collection_meta,
                decks=deck_metas,
                cards=compiled_cards,
                source_root=collection_dir,
                format="v2",
            )
        )
    return results


def compile_collection_dir(collection_dir: Path) -> CompiledCollection:
    collection_dir = collection_dir.expanduser().resolve()
    collection, decks, cards, rules = load_collection(collection_dir)
    collection_meta, deck_metas, compiled_cards = resolve_collection(
        collection,
        decks,
        cards,
    )
    validate_cards(compiled_cards, rules)
    return CompiledCollection(
        collection=collection_meta,
        decks=deck_metas,
        cards=compiled_cards,
        source_root=collection_dir,
        format="v2",
    )


def write_compiled_output(collections: list[CompiledCollection], output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for compiled in collections:
        slug = "legacy" if compiled.collection is None else compiled.collection.collection_id
        out_path = output_dir / f"{slug}.json"
        payload = {
            "format": compiled.format,
            "collection": _serialize(compiled.collection),
            "decks": [_serialize(d) for d in compiled.decks],
            "cards": [_serialize(c) for c in compiled.cards],
        }
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        written.append(out_path)
    return written


def _serialize(obj: object) -> dict[str, object]:
    if obj is None:
        return {}
    from dataclasses import asdict, is_dataclass

    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)
    raise TypeError(f"Cannot serialize {type(obj)!r}")
