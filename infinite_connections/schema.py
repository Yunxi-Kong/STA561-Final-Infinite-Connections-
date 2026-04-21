"""Data models and JSON schema helpers for Connections-style puzzles."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


DIFFICULTIES = {"yellow", "green", "blue", "purple"}
STATUSES = {"publish", "revise", "reject"}


@dataclass(slots=True)
class PuzzleGroup:
    """One answer group in a Connections-style puzzle."""

    id: str
    category: str
    words: list[str]
    difficulty: str
    strategy: str
    explanation: str

    def normalized_words(self) -> list[str]:
        return [normalize_word(word) for word in self.words]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category,
            "words": self.words,
            "difficulty": self.difficulty,
            "strategy": self.strategy,
            "explanation": self.explanation,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PuzzleGroup":
        return cls(
            id=str(data["id"]),
            category=str(data["category"]),
            words=[str(word) for word in data["words"]],
            difficulty=str(data.get("difficulty", "green")).lower(),
            strategy=str(data.get("strategy", "semantic")),
            explanation=str(data.get("explanation", "")),
        )


@dataclass(slots=True)
class Puzzle:
    """A complete candidate puzzle."""

    id: str
    title: str
    theme: str
    words: list[str]
    groups: list[PuzzleGroup]
    source_strategy: str
    curator_note: str
    decoy_notes: list[str] = field(default_factory=list)
    image_prompt: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def normalized_words(self) -> list[str]:
        return [normalize_word(word) for word in self.words]

    def answer_map(self) -> dict[str, str]:
        mapping: dict[str, str] = {}
        for group in self.groups:
            for word in group.words:
                mapping[normalize_word(word)] = group.id
        return mapping

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "theme": self.theme,
            "words": self.words,
            "groups": [group.to_dict() for group in self.groups],
            "source_strategy": self.source_strategy,
            "curator_note": self.curator_note,
            "decoy_notes": self.decoy_notes,
            "image_prompt": self.image_prompt,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Puzzle":
        return cls(
            id=str(data["id"]),
            title=str(data["title"]),
            theme=str(data.get("theme", "")),
            words=[str(word) for word in data["words"]],
            groups=[PuzzleGroup.from_dict(group) for group in data["groups"]],
            source_strategy=str(data.get("source_strategy", "mixed")),
            curator_note=str(data.get("curator_note", "")),
            decoy_notes=[str(note) for note in data.get("decoy_notes", [])],
            image_prompt=str(data.get("image_prompt", "")),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass(slots=True)
class ValidationIssue:
    severity: str
    code: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"severity": self.severity, "code": self.code, "message": self.message}


@dataclass(slots=True)
class QualityReport:
    puzzle_id: str
    status: str
    quality_score: float
    components: dict[str, float]
    issues: list[ValidationIssue]
    rejection_reasons: list[str]
    nearest_reference: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "puzzle_id": self.puzzle_id,
            "status": self.status,
            "quality_score": round(self.quality_score, 2),
            "components": {key: round(value, 2) for key, value in self.components.items()},
            "issues": [issue.to_dict() for issue in self.issues],
            "rejection_reasons": self.rejection_reasons,
            "nearest_reference": self.nearest_reference,
        }


def normalize_word(word: str) -> str:
    return " ".join(word.strip().upper().split())


PUZZLE_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "id",
        "title",
        "theme",
        "words",
        "groups",
        "source_strategy",
        "curator_note",
        "decoy_notes",
        "image_prompt",
        "metadata",
    ],
    "properties": {
        "id": {"type": "string"},
        "title": {"type": "string"},
        "theme": {"type": "string"},
        "words": {"type": "array", "minItems": 16, "maxItems": 16, "items": {"type": "string"}},
        "groups": {
            "type": "array",
            "minItems": 4,
            "maxItems": 4,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["id", "category", "words", "difficulty", "strategy", "explanation"],
                "properties": {
                    "id": {"type": "string"},
                    "category": {"type": "string"},
                    "words": {"type": "array", "minItems": 4, "maxItems": 4, "items": {"type": "string"}},
                    "difficulty": {"type": "string", "enum": sorted(DIFFICULTIES)},
                    "strategy": {"type": "string"},
                    "explanation": {"type": "string"},
                },
            },
        },
        "source_strategy": {"type": "string"},
        "curator_note": {"type": "string"},
        "decoy_notes": {"type": "array", "items": {"type": "string"}},
        "image_prompt": {"type": "string"},
        "metadata": {"type": "object"},
    },
}
