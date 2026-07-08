# Deckflow Markdown Format (v1)

> **Recommended:** New decks should use the [v2 Deck Project format](DECK_PROJECT.md) (YAML manifests + one card per file). v1 monolithic markdown remains fully supported.

Deckflow v1 decks are plain Markdown files designed for **git-native workflows**: human-readable, diff-friendly, and structured enough for reliable import, re-import, and linking to code.

This document is the canonical v1 spec. The reference implementation lives in [`examples/legacy/advanced_sample_deck.md`](../examples/legacy/advanced_sample_deck.md).

---

## Design goals

| Goal | How v1 achieves it |
|------|---------------------|
| Stable re-imports | Stable `card id` slugs + collection `id` |
| Hierarchy | `## Deck: A::B::C` paths (Anki-style subdecks) |
| Inheritance | Collection/deck tags cascade to cards |
| Engineer workflow | `Links` to LeetCode problems, files, URLs |
| Scheduling hints | `config` blocks at collection/deck/card level |
| Auditability | `source`, `notes`, `status`, `priority` metadata |
| Git diffs | One card per `---` block; avoid reflowing whole file |

---

## File structure

```
┌─────────────────────────────────────┐
│  YAML frontmatter (collection)      │  ← required in v1
├─────────────────────────────────────┤
│  # Title + optional prose intro     │  ← human docs only
├─────────────────────────────────────┤
│  ## Deck: path::to::subdeck         │
│    deck metadata fields             │
│                                     │
│  ### Card: stable-slug              │
│    card metadata fields             │
│    **Front:** …                     │
│    **Back:** …                      │
│  ---                                │
│  ### Card: next-slug                │
│  ---                                │
├─────────────────────────────────────┤
│  ## Deck: next::section             │
│  …                                  │
└─────────────────────────────────────┘
```

**Card separator:** `---` on its own line between cards (not required after the last card in a deck).

**Legacy format:** Files *without* `deckflow: 1` frontmatter still import using the older `### Card 1` numbered style (backward compatible).

---

## 1. Collection frontmatter (required in v1)

Every v1 deck file **must** begin with YAML frontmatter delimited by `---`.

```yaml
---
deckflow: 1                          # REQUIRED — format version
id: python-de-interview              # REQUIRED — stable collection id (slug)
title: Python Data Engineering Interview
description: |
  Spaced repetition deck for Python fundamentals,
  interview patterns, and DE mappings.
author: your-name
version: 1.0.0
created: 2026-07-08
updated: 2026-07-08
tags: [python, interview, data-engineering]
config:
  new_per_day: 20
  max_reviews_per_day: 150
  desired_retention: 0.9
  review_order: deck                 # deck | random
  bury_related: false
sources:
  - label: LeetCode repo
    path: ../LeetCode
  - label: Study notes
    path: ./notes
---
```

### Collection fields

| Field | Required | Description |
|-------|----------|-------------|
| `deckflow` | yes | Must be `1` for this spec |
| `id` | yes | Stable slug for the collection (`[a-z0-9-]+`) |
| `title` | yes | Display name |
| `description` | no | Multi-line summary (shown in UI/docs) |
| `author` | no | Creator |
| `version` | no | Semver for deck content, not format |
| `created` / `updated` | no | ISO dates (`YYYY-MM-DD`) |
| `tags` | no | Default tags applied to all cards (unless overridden) |
| `config` | no | Scheduling/behavior defaults (see [Config](#config-keys)) |
| `sources` | no | External repos/paths this deck references |

After frontmatter, an optional Markdown heading and prose block document the deck for humans. This content is **not imported as cards**.

---

## 2. Deck sections

Each deck begins with a level-2 heading:

```markdown
## Deck: Python::01 Fundamentals::Variables & Types
```

- **Path syntax:** `Segment::Segment::Subdeck` (double-colon hierarchy).
- Paths must be unique within a file.
- Order in the file is preserved for `review_order: deck`.

### Deck metadata fields

Place these lines immediately after the `## Deck:` heading, before any cards:

```markdown
**Deck description:** Immutable vs mutable types, identity, and truthiness.
**Deck tags:** `syntax` `fundamentals`
**Deck config:**
```yaml
new_per_day: 10
inherit_tags: true
```
```

| Field | Description |
|-------|-------------|
| `**Deck description:**` | Short summary of this subdeck |
| `**Deck tags:**` | Tags merged into each card (see inheritance) |
| `**Deck config:**` | YAML block overriding collection `config` for this deck |

---

## 3. Cards

Each card uses a level-3 heading with a **stable slug**:

```markdown
### Card: py-001-immutable-types
```

- Slug format: `[a-z0-9][a-z0-9-]*` (lowercase, hyphens).
- Used for idempotent import — renaming a slug creates a new card; changing front/back updates in place.
- Optional numeric prefix (`py-001-…`) keeps cards sortable in git.

### Card metadata fields

```markdown
**Card id:** `py-001`
**Type:** recognition
**Tags:** `syntax` `immutable`
**Priority:** high
**Status:** active
**Links:** `lc347` `file:../../lc/lc347.py` `url:https://docs.python.org/3/`
**Hint:** Think about hashability too.
**Notes:** Author-only context. Not shown during review by default.
**Source:** Python docs — Built-in Types
**Card config:**
```yaml
suspend: false
related: [py-002-mutable-types]
```
```

| Field | Values | Description |
|-------|--------|-------------|
| `**Card id:**` | slug | Explicit id; defaults to slug from `### Card:` heading |
| `**Type:**` | see below | Card cognitive mode |
| `**Tags:**` | list | Card-specific tags (merged with deck/collection) |
| `**Priority:**` | `low` `normal` `high` | Study ordering hint |
| `**Status:**` | `active` `suspended` | `suspended` cards import but are not scheduled |
| `**Links:**` | list | External references (see [Links](#links)) |
| `**Hint:**` | markdown | Optional pre-reveal hint |
| `**Notes:**` | markdown | Author notes stored as metadata |
| `**Source:**` | text | Citation / origin |
| `**Card config:**` | yaml | Per-card overrides |

### v1.1 learning fields (Deckflow analytics)

These fields power concept mastery, weak-spot detection, and the smart queue:

```markdown
**Concepts:** `python::fundamentals` `types::mutability`
**Prerequisites:** `py-001` `py-002`
**Difficulty:** 3
**Objective:** Explain mutability vs immutability in interview context
```

| Field | Description |
|-------|-------------|
| `**Concepts:**` | Hierarchical domain slugs (`domain::topic`) for mastery tracking |
| `**Prerequisites:**` | Card ids that should be learned first (phase 2 graph) |
| `**Difficulty:**` | Author estimate 1–5; informs queue weighting |
| `**Objective:**` | What "mastery" means for this card — used in analytics UI |

- `**Concepts:**` are stored in the learning graph; `**Tags:**` remain for filtering.
- If `**Concepts:**` is omitted, tags are used as concepts automatically.

### Card types

| Type | Use when |
|------|----------|
| `recognition` | Identify concept from prompt |
| `recall` | Produce answer from scratch |
| `pitfall` | Common mistake / bug pattern |
| `output` | Predict program output |
| `pattern` | Algorithm / design pattern |
| `complexity` | Big-O / space analysis |
| `mental-model` | Conceptual framing |
| `mapping` | Link two domains (e.g. LC ↔ DE) |

### Front and back (required)

```markdown
**Front:**
> Which Python types are **immutable**?

**Back:**
```
int, float, bool, str, tuple, frozenset
```
Tuples are immutable but may contain mutable objects.
```

**Content rules:**
- `**Front:**` and `**Back:**` are required.
- Body may be blockquote (`>`), fenced code, or plain Markdown.
- Text after a closing code fence on the back is included (explanations).
- `**Extra:**` is an alias for supplemental back content (appended to back).

---

## 4. Tag inheritance

Final card tags = merge of:

1. Collection `tags` (frontmatter)
2. `**Deck tags:**` (if `inherit_tags` is not `false`)
3. `**Tags:**` on the card

Duplicates are removed; order is collection → deck → card.

---

## 5. Config keys

Supported in collection, deck, or card `config` blocks. Child overrides parent.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `new_per_day` | int | — | Suggested new cards per day |
| `max_reviews_per_day` | int | — | Review cap |
| `desired_retention` | float | `0.9` | FSRS target retention |
| `review_order` | string | `deck` | `deck` or `random` |
| `bury_related` | bool | `false` | Bury siblings after review |
| `inherit_tags` | bool | `true` | Deck tags cascade to cards |
| `suspend` | bool | `false` | Skip scheduling |
| `related` | list | `[]` | Related card ids |

---

## 6. Links

Syntax in `**Links:**`:

| Form | Example | Meaning |
|------|---------|---------|
| LeetCode shorthand | `` `lc347` `` | LeetCode problem 347 |
| File path | `` `file:../../lc/lc347.py` `` | Relative file in repo |
| URL | `` `url:https://…` `` | External reference |
| Test command | `` `test:pytest lc/test_347.py` `` | Runnable hook (phase 2) |

Links are stored as metadata for future UI/CLI integration.

---

## 7. Import behavior

| Scenario | Behavior |
|----------|----------|
| First import | Create decks + cards + FSRS scheduling rows |
| Re-import same file | Upsert by `(deck_path, card_uid)` or `(deck_path, card_index)` for legacy |
| Changed front/back | Update content, **preserve** review history |
| Renamed card slug | Treated as new card |
| `status: suspended` | Imported; excluded from due queue |
| Missing front/back | Card skipped with warning |

---

## 8. Naming conventions

```
collection id:   python-de-interview
deck path:       Python::01 Fundamentals::Variables & Types
card slug:       py-001-immutable-types
card id:         py-001
```

Recommended prefixes by domain:

| Prefix | Domain |
|--------|--------|
| `py-` | Python language |
| `pd-` | Pandas |
| `sql-` | SQL |
| `lc-` | LeetCode mapping |
| `sys-` | System design |

---

## 9. Minimal v1 example

```markdown
---
deckflow: 1
id: demo
title: Demo Deck
tags: [demo]
config:
  new_per_day: 10
---

# Demo Deck

## Deck: Demo::Basics

**Deck description:** Tiny example deck.

### Card: demo-001-hello

**Type:** recognition
**Tags:** `intro`

**Front:**
> What is 2 + 2?

**Back:**
```
4
```

---
```

---

## 10. Migrating from legacy format

Legacy files (like `PYTHON_DECK.md`) use `### Card 1` without frontmatter. To migrate:

1. Add collection frontmatter with `deckflow: 1` and stable `id`.
2. Rename `### Card N` → `### Card: py-NNN-short-slug`.
3. Add `**Card id:**` matching your numbering scheme.
4. Group existing `**Tags:**` / `**Type:**` as-is — they still work.
5. Optionally add `**Links:**`, `**Deck description:**`, and `config` blocks.

Deckflow accepts **both** formats during transition.

---

## 11. Validation checklist

Before committing a deck file:

- [ ] `deckflow: 1` and `id` in frontmatter
- [ ] Every deck has `## Deck: …` path
- [ ] Every card has unique slug in file
- [ ] Every card has `**Front:**` and `**Back:**`
- [ ] Tags use backtick form for consistency
- [ ] `---` between cards
- [ ] Card ids sortable / prefixed (`py-001`, `py-002`, …)
