# Deck Project (v2)

Deckflow v2 organizes learning decks as a **project** — similar to how [dbt](https://www.getdbt.com/) organizes SQL models. Metadata lives in YAML; card content stays markdown for readable git diffs.

## Quick start

```bash
# Scaffold a new project
deckflow init-project my-learning

# Validate structure and card rules
deckflow validate my-learning

# Import into local SQLite
deckflow init
deckflow import my-learning
```

## Project layout

```
my-learning/
  deckflow.yaml                    # project manifest
  collections/
    my-collection/
      collection.yaml              # collection metadata + scheduling config
      schema.yaml                  # optional validation rules
      decks/
        fundamentals.yaml          # deck path, tags, config
      cards/
        sample-001.md              # one card per file
```

## Card file format

Each card is a markdown file with YAML frontmatter and front/back sections:

```markdown
---
id: py-001
deck: Python::01 Fundamentals::Variables
type: recognition
concepts: [python::fundamentals]
tags: [immutable]
difficulty: 2
priority: high
links:
  - url:https://docs.python.org/3/library/stdtypes.html
---

Which Python types are **immutable**?

---

```
int, float, bool, str, tuple, frozenset
```
```

- **Frontmatter** — all metadata (validated by Pydantic on `deckflow validate`)
- **Body** — split on a standalone `---` line: front above, back below

## Project manifest (`deckflow.yaml`)

```yaml
deckflow: 2
name: my-learning
version: 1.0.0
collections:
  - path: collections/my-collection
defaults:
  config:
    new_per_day: 20
    max_reviews_per_day: 150
```

## Collection spec (`collection.yaml`)

```yaml
deckflow: 2
id: my-collection
title: My Learning Collection
tags: [python]
config:
  new_per_day: 20
  desired_retention: 0.9
  review_order: deck
tracks:
  - id: fundamentals-first
    title: Fundamentals First
    description: Start here before advanced topics
    steps:
      - type: deck
        match: Python::01 Fundamentals::*
      - type: concept
        slug: pattern::heap
```

## Deck spec (`decks/*.yaml`)

```yaml
path: Python::01 Fundamentals::Variables
description: Core types and mutability
tags: [fundamentals]
config:
  new_per_day: 10
  inherit_tags: true
```

## CLI workflow

| Command | Purpose |
|---------|---------|
| `deckflow init-project <name>` | Scaffold empty v2 project |
| `deckflow validate <path>` | Validate project, collection, or markdown file |
| `deckflow compile <path>` | Write compiled JSON to `.deckflow/compiled/` |
| `deckflow import <path>` | Auto-detect and import (v2 project, collection, or v1 `.md`) |
| `deckflow migrate <file.md> <out-dir>` | Convert v1 monolithic deck to v2 project |

## Validation (`schema.yaml`)

Optional per-collection rules:

```yaml
cards:
  id:
    unique: true
    pattern: "^[a-z0-9-]+$"
  concepts:
    required: true
  prerequisites:
    references: cards
```

Run with `deckflow validate collections/my-collection`.

## Learning Map (user-facing organization)

After import, Deckflow exposes a **Learning Library** — a mental model for studying without reading raw `deck_path` strings:

| User term | Data source | Example |
|-----------|-------------|---------|
| **Collection** | `collections` table | Python DE Interview |
| **Module** | `decks.path` split on `::` | Python → 01 Fundamentals → Variables & Types |
| **Topic** | `concepts` tree (`slug`, `label`) | `python::fundamentals`, `pattern::heap` |
| **Track** | Optional `tracks` in `collection.yaml` | "Fundamentals First" ordered path |

### Study tracks

Optional curated paths in `collection.yaml` (see example above). Each step is either a deck prefix (`match: Python::01 Fundamentals::*`) or a concept (`slug: pattern::heap`). Progress shows due cards cleared per step.

### Focus Mode

Review only a module subtree and/or topic:

```bash
deckflow library                    # tree view of modules, topics, tracks
deckflow review --deck "Python::01 Fundamentals"
deckflow review --topic pattern::heap
deckflow review --track fundamentals-first
deckflow stats --by-deck
```

Web UI: open **Library** (`/library`) or add `?deck=` / `?concept=` to `/review`.

## Migrating from v1

v1 monolithic markdown (`deckflow: 1` frontmatter) remains supported indefinitely.

```bash
deckflow migrate examples/legacy/advanced_sample_deck.md examples/
deckflow validate examples/python-de-interview
deckflow import examples/python-de-interview
```

See also:

- [`docs/DECK_FORMAT.md`](DECK_FORMAT.md) — v1 markdown spec (legacy supported)
- [`examples/python-de-interview/`](../../examples/python-de-interview/) — reference v2 project
- [`examples/legacy/`](../../examples/legacy/) — v1 and legacy examples

## Inheritance

Config and tags cascade:

```
project.defaults.config → collection.config → deck.config → card.config
collection.tags ∪ deck.tags ∪ card.tags (when inherit_tags: true)
```

## For maintainers

Compile pipeline lives in `deckflow/compiler/`:

```
deckflow.yaml → loader → resolver → validator → CompiledCollection → import_service
```

Format adapters in `deckflow/extract/`; Pydantic schemas in `deckflow/schemas/`.
