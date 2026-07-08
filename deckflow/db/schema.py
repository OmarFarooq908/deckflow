SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    description TEXT,
    config_json TEXT NOT NULL DEFAULT '{}',
    meta_json TEXT NOT NULL DEFAULT '{}',
    source_file TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS decks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT NOT NULL,
    source_file TEXT NOT NULL,
    collection_id INTEGER REFERENCES collections(id) ON DELETE SET NULL,
    meta_json TEXT NOT NULL DEFAULT '{}',
    UNIQUE(path, source_file)
);

CREATE TABLE IF NOT EXISTS concepts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    label TEXT NOT NULL,
    parent_id INTEGER REFERENCES concepts(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    deck_id INTEGER NOT NULL REFERENCES decks(id) ON DELETE CASCADE,
    front_md TEXT NOT NULL,
    back_md TEXT NOT NULL,
    card_type TEXT,
    tags_json TEXT NOT NULL DEFAULT '[]',
    source_line INTEGER NOT NULL,
    card_index INTEGER NOT NULL,
    card_uid TEXT,
    meta_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(deck_id, card_index)
);

CREATE TABLE IF NOT EXISTS card_concepts (
    card_id INTEGER NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    concept_id INTEGER NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    weight REAL NOT NULL DEFAULT 1.0,
    PRIMARY KEY (card_id, concept_id)
);

CREATE TABLE IF NOT EXISTS scheduling (
    card_id INTEGER PRIMARY KEY REFERENCES cards(id) ON DELETE CASCADE,
    due TEXT NOT NULL,
    fsrs_json TEXT NOT NULL,
    reps INTEGER NOT NULL DEFAULT 0,
    lapses INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS review_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    cards_reviewed INTEGER NOT NULL DEFAULT 0,
    collection_id INTEGER REFERENCES collections(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id INTEGER NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    session_id INTEGER REFERENCES review_sessions(id) ON DELETE SET NULL,
    rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 4),
    reviewed_at TEXT NOT NULL,
    elapsed_ms INTEGER,
    reveal_ms INTEGER,
    rating_ms INTEGER,
    retrievability REAL,
    stability REAL,
    difficulty REAL,
    state INTEGER,
    fsrs_snapshot_json TEXT
);

CREATE TABLE IF NOT EXISTS concept_mastery (
    concept_id INTEGER PRIMARY KEY REFERENCES concepts(id) ON DELETE CASCADE,
    card_count INTEGER NOT NULL DEFAULT 0,
    reviews_count INTEGER NOT NULL DEFAULT 0,
    retention_7d REAL NOT NULL DEFAULT 0,
    retention_30d REAL NOT NULL DEFAULT 0,
    mastery_score REAL NOT NULL DEFAULT 0,
    weakness_score REAL NOT NULL DEFAULT 0,
    last_reviewed_at TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_scheduling_due ON scheduling(due);
CREATE INDEX IF NOT EXISTS idx_reviews_reviewed_at ON reviews(reviewed_at);
CREATE INDEX IF NOT EXISTS idx_reviews_card_id ON reviews(card_id);
CREATE INDEX IF NOT EXISTS idx_card_concepts_concept ON card_concepts(concept_id);
"""
