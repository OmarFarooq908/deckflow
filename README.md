# Deckflow

[![CI](https://github.com/OmarFarooq908/deckflow/actions/workflows/ci.yml/badge.svg)](https://github.com/OmarFarooq908/deckflow/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Deckflow** — data-centric spaced repetition for engineers who learn in git. Import markdown decks, capture rich review telemetry, track domain mastery, and get an intelligent daily study queue.

> **Status:** Early open source (alpha). APIs and deck format may evolve before 1.0.

## What makes Deckflow different

- **Maximum data** — every review records timing, retrievability, and FSRS state snapshots
- **Domain mastery** — concept-level retention and weakness scores
- **Smart queue** — prioritized by due urgency, weak concepts, and card priority
- **Git-native decks** — v1 markdown format with concepts, objectives, and links

## Quickstart

```bash
# Install (from repo root)
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Initialize local database (~/.deckflow/deckflow.db)
deckflow init

# Import the reference deck
deckflow import examples/advanced_sample_deck.md

# Review due cards in the terminal
deckflow review --limit 20

# View stats
deckflow stats
```

## Web UI

```bash
# Terminal 1 — API on http://localhost:5174
deckflow serve

# Terminal 2 — Vite dev server on http://localhost:5173
cd web && npm ci && npm run dev
```

Open **http://localhost:5173** in the browser (not 5174 — that port is the API).
If Vite says port 5173 is in use, stop the other process first (`lsof -i :5173`) so the UI and API stay on separate ports.

## Markdown deck format

Deckflow supports legacy `## Deck:` / `### Card` markdown and the **recommended v1 format** (frontmatter, stable card ids, links, config):

- [`docs/DECK_FORMAT.md`](docs/DECK_FORMAT.md) — full specification
- [`examples/advanced_sample_deck.md`](examples/advanced_sample_deck.md) — comprehensive reference deck
- [`examples/sample_deck.md`](examples/sample_deck.md) — minimal legacy example

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DECKFLOW_DB` | `~/.deckflow/deckflow.db` | SQLite database path |

Override per command with `--db /path/to/deckflow.db`.

## Architecture

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for layers, data flow, and extension points.

- **Core** (`deckflow/`) — parser, SQLite storage, FSRS scheduler, shared services
- **CLI** (`cli/`) — Typer commands
- **API** (`api/`) — FastAPI for the web UI
- **Web** (`web/`) — Vite + React review interface

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, quality checks, and PR guidelines.

- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security policy](SECURITY.md)
- [Changelog](CHANGELOG.md)

## License

[MIT](LICENSE) — Copyright (c) 2026 Omar Farooq
