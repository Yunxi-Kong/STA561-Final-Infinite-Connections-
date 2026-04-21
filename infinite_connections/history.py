"""Reference-data utilities for duplicate and near-duplicate checks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .schema import Puzzle, normalize_word


def load_reference_sets(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    references = data.get("references", data if isinstance(data, list) else [])
    normalized: list[dict[str, Any]] = []
    for item in references:
        words = item.get("words", [])
        normalized.append(
            {
                "id": item.get("id", "reference"),
                "title": item.get("title", "reference"),
                "words": sorted({normalize_word(str(word)) for word in words}),
            }
        )
    return normalized


def nearest_reference(puzzle: Puzzle, references: list[dict[str, Any]]) -> dict[str, Any] | None:
    puzzle_words = set(puzzle.normalized_words())
    best: dict[str, Any] | None = None
    best_similarity = 0.0
    for reference in references:
        reference_words = set(reference.get("words", []))
        if not reference_words:
            continue
        union = puzzle_words | reference_words
        similarity = len(puzzle_words & reference_words) / len(union)
        if similarity > best_similarity:
            best_similarity = similarity
            best = {
                "id": reference.get("id", "reference"),
                "title": reference.get("title", "reference"),
                "similarity": similarity,
                "overlap": sorted(puzzle_words & reference_words),
            }
    return best
