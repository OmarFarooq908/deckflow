from __future__ import annotations

from pathlib import Path

import yaml

from deckflow.schemas.specs import CardSpec


def parse_card_file(path: Path, text: str | None = None) -> CardSpec:
    """Parse a v2 card file: YAML frontmatter + front/back body separated by ---."""
    raw = text if text is not None else path.read_text(encoding="utf-8")
    if not raw.startswith("---"):
        raise ValueError(f"Card file must start with YAML frontmatter: {path}")

    end = raw.find("\n---", 3)
    if end == -1:
        raise ValueError(f"Card file missing closing frontmatter delimiter: {path}")

    frontmatter = yaml.safe_load(raw[3:end].strip()) or {}
    body = raw[end + 4 :].lstrip("\n")

    front_md, back_md = _split_front_back(body, path)
    frontmatter["front_md"] = front_md
    frontmatter["back_md"] = back_md
    frontmatter["source_file"] = str(path)
    frontmatter["source_line"] = 1

    return CardSpec.model_validate(frontmatter)


def _split_front_back(body: str, path: Path) -> tuple[str, str]:
    """Split card body on first standalone --- line."""
    lines = body.splitlines()
    separator_idx: int | None = None
    for idx, line in enumerate(lines):
        if line.strip() == "---":
            separator_idx = idx
            break

    if separator_idx is None:
        raise ValueError(f"Card file missing front/back separator (---): {path}")

    front = "\n".join(lines[:separator_idx]).strip()
    back = "\n".join(lines[separator_idx + 1 :]).strip()
    if not front or not back:
        raise ValueError(f"Card file must have non-empty front and back sections: {path}")
    return front, back
