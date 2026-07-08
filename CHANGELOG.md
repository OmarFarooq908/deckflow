# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-07-08

### Added

- Data-centric learning platform: collections, concepts, concept mastery
- Rich review telemetry (reveal_ms, rating_ms, retrievability, FSRS snapshots)
- Smart daily queue with explainable prioritization
- Analytics API (`/analytics/*`, `/study-plan/today`)
- Analytics dashboard in web UI (mastery, weak spots, today's plan)
- Deckflow Markdown v1.1 fields: Concepts, Prerequisites, Difficulty, Objective

## [0.1.0] - 2026-07-08

### Added

- Local-first SRS with FSRS scheduling
- Markdown deck import (legacy and v1 formats)
- Typer CLI (`init`, `import`, `review`, `stats`, `serve`)
- FastAPI backend and Vite + React web UI
- SQLite persistence with idempotent re-import

[Unreleased]: https://github.com/OmarFarooq908/deckflow/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/OmarFarooq908/deckflow/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/OmarFarooq908/deckflow/releases/tag/v0.1.0
