from __future__ import annotations


class ConceptsMixin:
    def upsert_concept(self, slug: str, label: str | None = None) -> int:
        conn = self.connect()
        label = label or slug.replace("::", " / ").replace("-", " ").title()
        parent_id = None
        if "::" in slug:
            parent_slug = slug.rsplit("::", 1)[0]
            parent_row = conn.execute(
                "SELECT id FROM concepts WHERE slug = ?", (parent_slug,)
            ).fetchone()
            parent_id = int(parent_row["id"]) if parent_row else self.upsert_concept(parent_slug)

        conn.execute(
            """
            INSERT INTO concepts (slug, label, parent_id)
            VALUES (?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET label = excluded.label
            """,
            (slug, label, parent_id),
        )
        row = conn.execute("SELECT id FROM concepts WHERE slug = ?", (slug,)).fetchone()
        assert row is not None
        conn.commit()
        return int(row["id"])

    def link_card_concepts(
        self,
        card_id: int,
        concept_slugs: list[str],
        weight: float = 1.0,
    ) -> None:
        conn = self.connect()
        conn.execute("DELETE FROM card_concepts WHERE card_id = ?", (card_id,))
        for slug in concept_slugs:
            concept_id = self.upsert_concept(slug)
            conn.execute(
                """
                INSERT INTO card_concepts (card_id, concept_id, weight)
                VALUES (?, ?, ?)
                """,
                (card_id, concept_id, weight),
            )
        conn.commit()

    def link_card_tags_as_concepts(self, card_id: int, tags: list[str]) -> None:
        if tags:
            self.link_card_concepts(card_id, tags, weight=0.5)
