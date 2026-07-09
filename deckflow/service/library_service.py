from __future__ import annotations

from dataclasses import dataclass, field

from deckflow.db.repository import Repository
from deckflow.models.domain import (
    CollectionSummary,
    ConceptMastery,
    LearningLibrary,
    LibraryNode,
    ReviewFocus,
    TrackStepSummary,
    TrackSummary,
)


@dataclass
class _TrieNode:
    label: str
    segment: str
    path_prefix: str
    due_count: int = 0
    card_count: int = 0
    children: dict[str, _TrieNode] = field(default_factory=dict)
    is_leaf: bool = False
    full_path: str | None = None


def get_learning_library(repo: Repository) -> LearningLibrary:
    collections = build_collection_summaries(repo)
    primary = _primary_collection_summary(collections)
    modules = build_module_tree(repo)
    topics = build_topic_tree(repo)
    tracks = build_track_summaries(repo)
    return LearningLibrary(
        collection=primary,
        collections=collections,
        modules=modules,
        topics=topics,
        tracks=tracks,
    )


def get_module_tree(repo: Repository) -> list[LibraryNode]:
    return build_module_tree(repo)


def get_topic_tree(repo: Repository) -> list[LibraryNode]:
    return build_topic_tree(repo)


def build_module_tree(repo: Repository) -> list[LibraryNode]:
    decks = repo.list_decks()
    root: dict[str, _TrieNode] = {}

    for deck in decks:
        parts = deck.path.split("::")
        prefix_parts: list[str] = []
        level = root
        for index, part in enumerate(parts):
            prefix_parts.append(part)
            prefix = "::".join(prefix_parts)
            if part not in level:
                level[part] = _TrieNode(
                    label=part,
                    segment=part,
                    path_prefix=prefix,
                )
            node = level[part]
            node.card_count += deck.card_count
            node.due_count += deck.due_count
            if index == len(parts) - 1:
                node.is_leaf = True
                node.full_path = deck.path
            level = node.children

    return [_trie_to_library_node(node) for node in sorted(root.values(), key=lambda n: n.label)]


def build_topic_tree(repo: Repository) -> list[LibraryNode]:
    concepts = repo.list_concept_mastery()
    parent_map = repo.get_concept_parent_map()
    children_map: dict[int | None, list[ConceptMastery]] = {}

    for concept in concepts:
        parent_id = parent_map.get(concept.concept_id)
        children_map.setdefault(parent_id, []).append(concept)

    def build_level(parent_id: int | None) -> list[LibraryNode]:
        nodes: list[LibraryNode] = []
        for concept in sorted(children_map.get(parent_id, []), key=lambda c: c.slug):
            child_nodes = build_level(concept.concept_id)
            due, total = _concept_card_counts(repo, concept.slug)
            nodes.append(
                LibraryNode(
                    id=concept.slug,
                    label=concept.label,
                    kind="topic",
                    slug=concept.slug,
                    due_count=due,
                    card_count=total,
                    mastery_score=concept.mastery_score,
                    children=child_nodes,
                )
            )
        return nodes

    roots = build_level(None)
    if roots:
        return roots

    return [
        LibraryNode(
            id=c.slug,
            label=c.label,
            kind="topic",
            slug=c.slug,
            due_count=_concept_card_counts(repo, c.slug)[0],
            card_count=c.card_count,
            mastery_score=c.mastery_score,
            children=[],
        )
        for c in sorted(concepts, key=lambda item: item.slug)
    ]


def build_track_summaries(repo: Repository) -> list[TrackSummary]:
    collections = repo.list_collections()
    if not collections:
        return []

    multi = len(collections) > 1
    summaries: list[TrackSummary] = []
    for collection in collections:
        tracks = collection.get("meta", {}).get("tracks", [])
        if not isinstance(tracks, list):
            continue
        for raw in tracks:
            if not isinstance(raw, dict):
                continue
            raw_track_id = str(raw.get("id", ""))
            if not raw_track_id:
                continue
            track_id = f"{collection['slug']}::{raw_track_id}" if multi else raw_track_id
            summaries.append(_build_track_summary(raw, track_id, repo))
    return summaries


def _build_track_summary(
    raw: dict[str, object],
    track_id: str,
    repo: Repository,
) -> TrackSummary:
    steps_raw = raw.get("steps", [])
    step_summaries: list[TrackStepSummary] = []
    current_step = 0
    if isinstance(steps_raw, list):
        for index, step in enumerate(steps_raw):
            if not isinstance(step, dict):
                continue
            step_type = str(step.get("type", "deck"))
            match = step.get("match") or step.get("slug") or ""
            due, total = _step_counts(repo, step_type, str(match))
            completed = due == 0 and total > 0
            step_summaries.append(
                TrackStepSummary(
                    step_index=index,
                    step_type=step_type,
                    match=str(match),
                    due_count=due,
                    card_count=total,
                    completed=completed,
                )
            )
            if not completed and current_step == index:
                current_step = index
            elif completed and index == current_step and index + 1 < len(steps_raw):
                current_step = index + 1

    focus_deck, focus_concept = _step_focus(step_summaries, current_step)
    description_raw = raw.get("description")
    description = description_raw if isinstance(description_raw, str) else None
    return TrackSummary(
        id=track_id,
        title=str(raw.get("title", track_id)),
        description=description,
        current_step=min(current_step, max(len(step_summaries) - 1, 0)),
        total_steps=len(step_summaries),
        steps=step_summaries,
        focus_deck_prefix=focus_deck,
        focus_concept_slug=focus_concept,
    )


def get_track_focus(repo: Repository, track_id: str) -> ReviewFocus | None:
    for track in build_track_summaries(repo):
        if track.id != track_id and not track.id.endswith(f"::{track_id}"):
            continue
        return ReviewFocus(
            deck_prefix=track.focus_deck_prefix,
            concept_slug=track.focus_concept_slug,
            track_id=track.id,
        )
    return None


def build_collection_summaries(repo: Repository) -> list[CollectionSummary]:
    summaries: list[CollectionSummary] = []
    for collection in repo.list_collections():
        summaries.append(
            CollectionSummary(
                id=collection["id"],
                slug=collection["slug"],
                title=collection["title"],
                description=collection.get("description"),
                due_count=repo.count_due_for_collection(collection["id"]),
                card_count=repo.count_total_cards_for_collection(collection["id"]),
            )
        )
    return summaries


def _primary_collection_summary(
    collections: list[CollectionSummary],
) -> CollectionSummary | None:
    if not collections:
        return None
    if len(collections) == 1:
        return collections[0]
    return CollectionSummary(
        id=collections[0].id,
        slug="all-collections",
        title="All collections",
        description=None,
        due_count=sum(collection.due_count for collection in collections),
        card_count=sum(collection.card_count for collection in collections),
    )


def _build_collection_summary(repo: Repository) -> CollectionSummary | None:
    return _primary_collection_summary(build_collection_summaries(repo))


def _trie_to_library_node(node: _TrieNode) -> LibraryNode:
    sorted_children = sorted(node.children.values(), key=lambda n: n.label)
    children = [_trie_to_library_node(child) for child in sorted_children]
    return LibraryNode(
        id=node.path_prefix,
        label=node.label,
        kind="module",
        path=node.full_path or node.path_prefix,
        due_count=node.due_count,
        card_count=node.card_count,
        children=children,
    )


def _concept_card_counts(repo: Repository, concept_slug: str) -> tuple[int, int]:
    due = repo.count_cards_for_concept(concept_slug, due_only=True)
    total = repo.count_cards_for_concept(concept_slug, due_only=False)
    return due, total


def _step_counts(repo: Repository, step_type: str, match: str) -> tuple[int, int]:
    if step_type == "concept":
        return _concept_card_counts(repo, match)
    due, total = repo.get_deck_stats_by_prefix(match)
    return due, total


def _step_focus(steps: list[TrackStepSummary], current_step: int) -> tuple[str | None, str | None]:
    if not steps or current_step >= len(steps):
        return None, None
    step = steps[current_step]
    if step.step_type == "concept":
        return None, step.match
    return step.match, None
