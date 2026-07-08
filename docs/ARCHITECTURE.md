# Architecture

Deckflow is a local-first, data-centric spaced repetition system. Markdown decks are
the source of truth; SQLite stores scheduling state, review telemetry, and derived
analytics.

## Layer overview

```
markdown deck
    → parser (legacy / v1)
    → import_service
    → repository (SQLite)
    → services (review, queue, analytics, stats)
    → cli / api (thin adapters)
    → web (React UI via FastAPI proxy)
```

## Core modules

| Layer | Path | Responsibility |
|-------|------|----------------|
| Parser | `deckflow/parser/` | Parse legacy and v1/v1.1 markdown into `ParsedDeck` |
| Models | `deckflow/models/` | Dataclasses for parsed input and DB rows |
| DB | `deckflow/db/` | Schema, migrations, all SQL in `repository.py` |
| Scheduler | `deckflow/scheduler/` | FSRS wrapper for card scheduling |
| Services | `deckflow/service/` | Business logic — import, review, queue, analytics |
| CLI | `cli/` | Typer commands for terminal workflow |
| API | `api/` | FastAPI REST endpoints for the web UI |
| Web | `web/` | React + Vite frontend |

## Data flow

### Import

1. `parse_markdown_deck_text()` detects v1 frontmatter or legacy format.
2. `import_service.import_deck()` upserts collections, decks, cards, and concepts.
3. `repository.upsert_card()` creates scheduling rows (new cards due immediately).

### Review

1. `queue_service.build_daily_queue()` scores due cards by urgency, weakness, priority.
2. `review_service.get_next_card()` returns the top queued card.
3. On rating, FSRS updates scheduling; telemetry is recorded; concept mastery refreshes.

### Analytics

- `concept_mastery` table stores per-concept retention and weakness scores.
- `analytics_service` aggregates overview stats, weak spots, and per-card history.
- `/study-plan/today` exposes the smart queue to the web UI.

## Extension points

| Change | Touch points |
|--------|--------------|
| New card field | `docs/DECK_FORMAT.md`, `deckflow/parser/v1.py`, `ParsedCard`, import path |
| New analytics | `repository.py` query + `analytics_service.py` + API route + web page |
| New CLI command | `cli/main.py` calling an existing service |
| Schema change | `deckflow/db/schema.py`, `_migrate()` in repository, tests |

## Maintainability rules

- **Service layer only** for business logic; CLI and API stay thin adapters.
- **No raw SQL outside** `deckflow/db/repository.py` (future: split into submodules).
- **Schema changes** require a migration in `_migrate()` plus a test.
- **Deck format changes** require spec + example deck + parser test.
- **Semver:** `0.x` until stable deck format + API; minor for features, patch for fixes.

## Future work

- Split `repository.py` (~800 lines) into `collections.py`, `concepts.py`, `reviews.py`
- Optional sync / multi-device support
- Plugin hooks for custom card renderers
