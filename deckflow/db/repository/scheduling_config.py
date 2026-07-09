from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from deckflow.compiler.resolver import merge_config
from deckflow.local_time import local_day_start


class SchedulingConfigMixin:
    def get_scheduling_config_for_deck(self, deck_id: int) -> dict[str, Any]:
        conn = self.connect()
        row = conn.execute("SELECT meta_json FROM decks WHERE id = ?", (deck_id,)).fetchone()
        deck_meta = json.loads(row["meta_json"] or "{}") if row else {}
        return merge_config(self.get_collection_config(), deck_meta.get("config", {}))

    def get_scheduling_config_for_card(self, card_id: int) -> dict[str, Any]:
        conn = self.connect()
        row = conn.execute(
            """
            SELECT c.deck_id, c.meta_json
            FROM cards c
            WHERE c.id = ?
            """,
            (card_id,),
        ).fetchone()
        if row is None:
            return self.get_collection_config()
        card_meta = json.loads(row["meta_json"] or "{}")
        deck_config = self.get_scheduling_config_for_deck(int(row["deck_id"]))
        return merge_config(deck_config, card_meta.get("card_config", {}))

    def count_new_cards_today_for_deck(
        self,
        deck_id: int,
        now: datetime | None = None,
    ) -> int:
        conn = self.connect()
        start = local_day_start(now)
        row = conn.execute(
            """
            SELECT COUNT(*) AS cnt
            FROM reviews r
            JOIN cards c ON c.id = r.card_id
            JOIN scheduling s ON s.card_id = r.card_id
            WHERE c.deck_id = ?
              AND s.reps = 1
              AND r.reviewed_at >= ?
            """,
            (deck_id, start.isoformat()),
        ).fetchone()
        return int(row["cnt"])
