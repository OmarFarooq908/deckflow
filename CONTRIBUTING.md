# Contributing to Deckflow

Thank you for your interest in contributing! Deckflow is a data-centric,
local-first spaced repetition tool for engineers who learn in git.

## Prerequisites

- Python 3.11 or 3.12
- Node.js 20+
- `make` (optional but recommended)

## Development setup

```bash
git clone https://github.com/OmarFarooq908/deckflow.git
cd deckflow

python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

cd web && npm ci && cd ..
```

## Quality checks

Run before opening a PR:

```bash
make check    # lint + test + web build
```

Individual targets:

```bash
make lint     # ruff, mypy, eslint
make test     # pytest with coverage (75% minimum)
make format   # auto-format Python with ruff
```

### Pre-commit hooks (recommended)

```bash
pip install pre-commit
pre-commit install
```

Hooks run ruff, mypy, and basic file hygiene on each commit.

## Pull request process

1. Fork the repo and create a branch from `main`
2. Make focused changes with tests
3. Update docs if you change behavior or deck format
4. Ensure `make check` passes
5. Open a PR with a clear description

### PR checklist

- [ ] Tests added or updated for behavior changes
- [ ] `make check` passes locally
- [ ] Docs updated if needed (README, `docs/DECK_FORMAT.md`, `docs/ARCHITECTURE.md`)
- [ ] CHANGELOG updated under `[Unreleased]` for user-facing changes
- [ ] No secrets, database files, or `node_modules` committed

## Deck format changes

If you modify the markdown deck format:

1. Update [`docs/DECK_FORMAT.md`](docs/DECK_FORMAT.md)
2. Update [`examples/advanced_sample_deck.md`](examples/advanced_sample_deck.md)
3. Add parser tests in `tests/`

## Architecture guidelines

- Business logic lives in `deckflow/service/` — keep `cli/` and `api/` thin
- SQL stays in `deckflow/db/repository.py`
- Schema changes need a migration in `_migrate()` plus a test
- See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full picture

## Commit messages

Use clear, imperative subjects:

```
Add concept mastery refresh on review
Fix deck tag inheritance for blank lines
```

## Questions

Open a [GitHub Discussion](https://github.com/OmarFarooq908/deckflow/discussions) or issue.

## Code of Conduct

This project follows the [Code of Conduct](CODE_OF_CONDUCT.md). By participating,
you agree to uphold it.
