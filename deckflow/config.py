from __future__ import annotations

import os
from pathlib import Path

DEFAULT_DB_DIR = Path.home() / ".deckflow"
DEFAULT_DB_PATH = DEFAULT_DB_DIR / "deckflow.db"


def get_db_path(override: str | None = None) -> Path:
    if override:
        return Path(override).expanduser().resolve()
    env_path = os.environ.get("DECKFLOW_DB")
    if env_path:
        return Path(env_path).expanduser().resolve()
    return DEFAULT_DB_PATH
