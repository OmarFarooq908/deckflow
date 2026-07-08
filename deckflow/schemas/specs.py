from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field, field_validator

SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")


class ProjectManifest(BaseModel):
    deckflow: int = Field(..., description="Must be 2 for v2 projects")
    name: str
    version: str = "1.0.0"
    collections: list[str] = Field(default_factory=list)
    defaults: dict[str, Any] = Field(default_factory=dict)

    @field_validator("deckflow")
    @classmethod
    def check_version(cls, value: int) -> int:
        if value != 2:
            raise ValueError("deckflow manifest version must be 2")
        return value


class TrackStepSpec(BaseModel):
    type: str
    match: str | None = None
    slug: str | None = None


class StudyTrackSpec(BaseModel):
    id: str
    title: str
    description: str | None = None
    steps: list[TrackStepSpec] = Field(default_factory=list)


class CollectionSpec(BaseModel):
    model_config = {"extra": "allow"}

    deckflow: int = 2
    id: str
    title: str
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    config: dict[str, Any] = Field(default_factory=dict)
    sources: list[dict[str, str]] = Field(default_factory=list)
    tracks: list[StudyTrackSpec] = Field(default_factory=list)

    @field_validator("id")
    @classmethod
    def check_id(cls, value: str) -> str:
        if not SLUG_PATTERN.match(value):
            raise ValueError(f"collection id must match {SLUG_PATTERN.pattern}")
        return value

    @property
    def meta(self) -> dict[str, Any]:
        reserved = {
            "deckflow",
            "id",
            "title",
            "description",
            "tags",
            "config",
            "sources",
            "tracks",
        }
        return {k: v for k, v in self.model_dump().items() if k not in reserved}


class DeckSpec(BaseModel):
    path: str
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    config: dict[str, Any] = Field(default_factory=dict)


class CardSpec(BaseModel):
    id: str
    deck: str
    type: str | None = None
    tags: list[str] = Field(default_factory=list)
    concepts: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)
    difficulty: int | None = Field(default=None, ge=1, le=5)
    objective: str | None = None
    priority: str | None = "normal"
    status: str = "active"
    links: list[str] = Field(default_factory=list)
    hint: str | None = None
    notes: str | None = None
    source: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    front_md: str = ""
    back_md: str = ""
    source_file: str | None = None
    source_line: int = 0

    @field_validator("id")
    @classmethod
    def check_id(cls, value: str) -> str:
        if not SLUG_PATTERN.match(value):
            raise ValueError(f"card id must match {SLUG_PATTERN.pattern}")
        return value

    @field_validator("priority")
    @classmethod
    def check_priority(cls, value: str | None) -> str | None:
        if value is None:
            return None
        allowed = {"high", "normal", "low"}
        lowered = value.lower()
        if lowered not in allowed:
            raise ValueError(f"priority must be one of {allowed}")
        return lowered

    @field_validator("status")
    @classmethod
    def check_status(cls, value: str) -> str:
        allowed = {"active", "suspended"}
        lowered = value.lower()
        if lowered not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return lowered


class FieldRule(BaseModel):
    unique: bool = False
    required: bool = False
    pattern: str | None = None
    references: str | None = None


class SchemaRules(BaseModel):
    cards: dict[str, FieldRule] = Field(default_factory=dict)
