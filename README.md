# Deckflow

[![CI](https://github.com/OmarFarooq908/deckflow/actions/workflows/ci.yml/badge.svg)](https://github.com/OmarFarooq908/deckflow/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Use LLMs to draft cards. Curate in git. Deckflow handles retention.**

Spaced repetition for engineers who learn in git — versioned deck projects, rich review telemetry, concept-level mastery, and a smart daily queue.

> **Status:** Early open source (alpha). v2 deck projects are the recommended format; v1 markdown import remains supported.

## What makes Deckflow different

- **Project-based decks** — dbt-inspired layout: YAML manifests + one card per markdown file
- **LLM-friendly markdown** — generate cards with AI, review diffs in git, import when ready
- **Maximum data** — every review records timing, retrievability, and FSRS state snapshots
- **Domain mastery** — concept-level retention and weakness scores
- **Smart queue** — prioritized by due urgency, weak concepts, and card priority
- **Git-native** — small, reviewable diffs; validate before import

## Quickstart

```bash
# Install (from repo root)
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Initialize local database (~/.deckflow/deckflow.db)
deckflow init

# Validate and import the reference v2 project
deckflow validate examples/python-de-interview
deckflow import examples/python-de-interview

# Review due cards in the terminal
deckflow review --limit 20

# Browse the learning map and focus review
deckflow library
deckflow review --deck "Python::01 Fundamentals"
deckflow stats --by-deck
```

### Create your own project

```bash
deckflow init-project my-learning
# edit collections/*/cards/*.md
deckflow validate my-learning
deckflow import my-learning
```

## Web UI

```bash
# One command — API + Vite (auto-picks free ports if 5173/5174 are taken)
make dev
# or: ./scripts/dev.sh
```

Defaults: web **http://localhost:5173**, API **http://localhost:5174**. The script prints the actual URLs if it moves to other ports.

Manual (two terminals):

```bash
deckflow serve          # API
cd web && npm run dev   # Vite — set DECKFLOW_API_PORT if the API is not on 5174
```

Open the **web** URL printed by the script (usually http://localhost:5173). Use **Library** to browse modules, topics, and study tracks; click **Review** on any node for focused study.

## LLM workflow

Deckflow does not call an LLM — the format is the integration. One card per `.md` file means any model can draft cards; you curate in git; Deckflow schedules review.

```text
Prompt → draft first-principles / Socratic cards as markdown
       → review and edit in git (deckflow validate)
       → deckflow import && deckflow review
```

See [`examples/python-de-interview/`](examples/python-de-interview/) for the reference deck layout.

## Deck formats

| Format | Status | Docs |
|--------|--------|------|
| **v2 Deck Project** | Recommended | [`docs/DECK_PROJECT.md`](docs/DECK_PROJECT.md) |
| v1 monolithic markdown | Supported | [`docs/DECK_FORMAT.md`](docs/DECK_FORMAT.md) |
| Legacy numbered cards | Supported | [`examples/legacy/sample_deck.md`](examples/legacy/sample_deck.md) |

Reference projects:

- [`examples/python-de-interview/`](examples/python-de-interview/) — v2 project (12 cards)
- [`examples/legacy/advanced_sample_deck.md`](examples/legacy/advanced_sample_deck.md) — v1 monolithic

Migrate v1 → v2: `deckflow migrate examples/legacy/advanced_sample_deck.md examples/`

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DECKFLOW_DB` | `~/.deckflow/deckflow.db` | SQLite database path |

Override per command with `--db /path/to/deckflow.db`.

## Architecture

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for layers, compile pipeline, and extension points.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, `make check`, and PR guidelines.

- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security policy](SECURITY.md)
- [Changelog](CHANGELOG.md)

## License

[MIT](LICENSE) — Copyright (c) 2026 Omar Farooq
