from __future__ import annotations

import re

from deckflow.schemas.compiled import CompiledCard
from deckflow.schemas.specs import SchemaRules


class ValidationError(Exception):
    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("\n".join(errors))


def validate_cards(cards: list[CompiledCard], rules: SchemaRules | None = None) -> None:
    errors: list[str] = []

    if not cards:
        errors.append("collection has no cards")
        validate_errors(errors)
        return

    card_ids = [c.card_uid for c in cards]
    id_set = set(card_ids)
    if len(id_set) != len(card_ids):
        seen: set[str] = set()
        for cid in card_ids:
            if cid in seen:
                errors.append(f"duplicate card id: {cid}")
            seen.add(cid)

    for card in cards:
        if not card.front_md.strip():
            errors.append(f"card {card.card_uid}: front is empty")
        if not card.back_md.strip():
            errors.append(f"card {card.card_uid}: back is empty")
        for prereq in card.prerequisites:
            if prereq not in id_set:
                errors.append(
                    f"card {card.card_uid}: prerequisite '{prereq}' references unknown card"
                )

    if rules:
        errors.extend(_apply_schema_rules(cards, rules))

    validate_errors(errors)


def validate_errors(errors: list[str]) -> None:
    if errors:
        raise ValidationError(errors)


def _apply_schema_rules(cards: list[CompiledCard], rules: SchemaRules) -> list[str]:
    errors: list[str] = []
    card_ids = [c.card_uid for c in cards]

    for field_name, rule in rules.cards.items():
        if rule.unique:
            seen: set[str] = set()
            for card in cards:
                value = _field_value(card, field_name)
                if value is None:
                    continue
                key = str(value)
                if key in seen:
                    errors.append(f"duplicate {field_name}: {key}")
                seen.add(key)

        if rule.required:
            for card in cards:
                value = _field_value(card, field_name)
                if value is None or value == [] or value == "":
                    errors.append(f"card {card.card_uid}: {field_name} is required")

        if rule.pattern:
            pattern = re.compile(rule.pattern)
            for card in cards:
                value = _field_value(card, field_name)
                if value is None:
                    continue
                if isinstance(value, list):
                    for item in value:
                        if not pattern.match(str(item)):
                            errors.append(
                                f"card {card.card_uid}: {field_name} '{item}' "
                                f"does not match {rule.pattern}"
                            )
                elif not pattern.match(str(value)):
                    errors.append(
                        f"card {card.card_uid}: {field_name} '{value}' "
                        f"does not match {rule.pattern}"
                    )

        if rule.references == "cards":
            id_set = set(card_ids)
            for card in cards:
                value = _field_value(card, field_name)
                if not value:
                    continue
                refs = value if isinstance(value, list) else [value]
                for ref in refs:
                    if str(ref) not in id_set:
                        errors.append(
                            f"card {card.card_uid}: {field_name} references unknown card '{ref}'"
                        )

    return errors


def _field_value(card: CompiledCard, field_name: str) -> object:
    mapping = {
        "id": card.card_uid,
        "deck": card.deck_path,
        "type": card.card_type,
        "tags": card.tags,
        "concepts": card.concepts,
        "prerequisites": card.prerequisites,
        "difficulty": card.difficulty,
        "priority": card.priority,
        "status": card.status,
    }
    return mapping.get(field_name)
