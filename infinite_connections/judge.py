"""LLM and offline judging utilities for generated puzzles."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from .schema import Puzzle
from .validator import score_puzzle


DEFAULT_JUDGE_MODEL = "gpt-5-nano"


JUDGE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "nyt_likeness",
        "clarity",
        "ambiguity_risk",
        "solver_confidence",
        "would_publish",
        "rationale",
        "possible_alternative_groups",
        "revision_suggestions",
    ],
    "properties": {
        "nyt_likeness": {"type": "number", "minimum": 0, "maximum": 100},
        "clarity": {"type": "number", "minimum": 0, "maximum": 100},
        "ambiguity_risk": {"type": "number", "minimum": 0, "maximum": 100},
        "solver_confidence": {"type": "number", "minimum": 0, "maximum": 100},
        "would_publish": {"type": "boolean"},
        "rationale": {"type": "string"},
        "possible_alternative_groups": {"type": "array", "items": {"type": "string"}},
        "revision_suggestions": {"type": "array", "items": {"type": "string"}},
    },
}

BATCH_JUDGE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["results"],
    "properties": {
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["puzzle_id", *JUDGE_SCHEMA["required"]],
                "properties": {
                    "puzzle_id": {"type": "string"},
                    **JUDGE_SCHEMA["properties"],
                },
            },
        }
    },
}


@dataclass(slots=True)
class JudgeResult:
    puzzle_id: str
    provider: str
    nyt_likeness: float
    clarity: float
    ambiguity_risk: float
    solver_confidence: float
    would_publish: bool
    rationale: str
    possible_alternative_groups: list[str]
    revision_suggestions: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "puzzle_id": self.puzzle_id,
            "provider": self.provider,
            "nyt_likeness": round(self.nyt_likeness, 2),
            "clarity": round(self.clarity, 2),
            "ambiguity_risk": round(self.ambiguity_risk, 2),
            "solver_confidence": round(self.solver_confidence, 2),
            "would_publish": self.would_publish,
            "rationale": self.rationale,
            "possible_alternative_groups": self.possible_alternative_groups,
            "revision_suggestions": self.revision_suggestions,
        }


def offline_judge(puzzle: Puzzle) -> JudgeResult:
    """Deterministic fallback judge used when live API calls are unavailable."""

    report = score_puzzle(puzzle)
    ambiguity = min(100.0, report.components.get("ambiguity_penalty", 0) * 9 + len(report.rejection_reasons) * 5)
    solver_confidence = max(0.0, min(100.0, report.quality_score - ambiguity * 0.2))
    would_publish = report.status == "publish" and ambiguity < 25
    suggestions = []
    if "weak_explanation" in report.rejection_reasons:
        suggestions.append("Write more concrete group explanations before manual review.")
    if "generic_category" in report.rejection_reasons:
        suggestions.append("Replace broad category labels with NYT-style concise labels.")
    if "surface_ambiguity" in report.rejection_reasons:
        suggestions.append("Run an ambiguity-focused solver and revise overlapping groups.")
    if not suggestions:
        suggestions.append("Send to manual review and compare against other accepted candidates.")
    return JudgeResult(
        puzzle_id=puzzle.id,
        provider="offline_heuristic",
        nyt_likeness=report.components.get("nyt_likeness", report.quality_score),
        clarity=report.components.get("clarity", report.quality_score),
        ambiguity_risk=ambiguity,
        solver_confidence=solver_confidence,
        would_publish=would_publish,
        rationale="Offline judge based on the deterministic validator and quality components.",
        possible_alternative_groups=[],
        revision_suggestions=suggestions,
    )


def openai_judge(puzzle: Puzzle, model: str | None = None) -> JudgeResult:
    """Judge one puzzle with a live OpenAI model using a strict JSON schema."""

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set.")
    try:
        from openai import OpenAI
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("Install optional dependencies with `python -m pip install -r requirements.txt`.") from exc

    client = OpenAI()
    review_model = model or os.getenv("OPENAI_JUDGE_MODEL", DEFAULT_JUDGE_MODEL)
    response = client.responses.create(  # pragma: no cover - live API path
        model=review_model,
        input=[
            {
                "role": "system",
                "content": (
                    "You are a skeptical editor for a NYT Connections-style puzzle generator. "
                    "Judge whether the puzzle is fair, original, and plausibly NYT-like. "
                    "Be stricter about ambiguity than about visual presentation."
                ),
            },
            {"role": "user", "content": build_judge_prompt(puzzle)},
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "connections_judge_result",
                "schema": JUDGE_SCHEMA,
                "strict": True,
            }
        },
    )
    data = json.loads(response.output_text)
    return JudgeResult(
        puzzle_id=puzzle.id,
        provider="openai",
        nyt_likeness=float(data["nyt_likeness"]),
        clarity=float(data["clarity"]),
        ambiguity_risk=float(data["ambiguity_risk"]),
        solver_confidence=float(data["solver_confidence"]),
        would_publish=bool(data["would_publish"]),
        rationale=str(data["rationale"]),
        possible_alternative_groups=[str(item) for item in data["possible_alternative_groups"]],
        revision_suggestions=[str(item) for item in data["revision_suggestions"]],
    )


def openai_judge_batch(puzzles: list[Puzzle], model: str | None = None) -> list[JudgeResult]:
    """Judge several puzzles in one live API call using a strict JSON schema."""

    if not puzzles:
        return []
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set.")
    try:
        from openai import OpenAI
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("Install optional dependencies with `python -m pip install -r requirements.txt`.") from exc

    review_model = model or os.getenv("OPENAI_JUDGE_MODEL", DEFAULT_JUDGE_MODEL)
    client = OpenAI()
    schema = json.loads(json.dumps(BATCH_JUDGE_SCHEMA))
    schema["properties"]["results"]["minItems"] = len(puzzles)
    schema["properties"]["results"]["maxItems"] = len(puzzles)
    response = client.responses.create(  # pragma: no cover - live API path
        model=review_model,
        input=[
            {
                "role": "system",
                "content": (
                    "You are a skeptical editor for a NYT Connections-style puzzle generator. "
                    "Judge whether each puzzle is fair, original, and plausibly NYT-like. "
                    "Return one result for every puzzle_id. Be stricter about ambiguity than visual presentation."
                ),
            },
            {"role": "user", "content": build_batch_judge_prompt(puzzles)},
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "connections_batch_judge_result",
                "schema": schema,
                "strict": True,
            }
        },
    )
    payload = json.loads(response.output_text)
    by_id = {str(item["puzzle_id"]): item for item in payload["results"]}
    results: list[JudgeResult] = []
    for puzzle in puzzles:
        data = by_id.get(puzzle.id)
        if not data:
            raise RuntimeError(f"Missing judge result for puzzle {puzzle.id}.")
        results.append(
            JudgeResult(
                puzzle_id=puzzle.id,
                provider="openai",
                nyt_likeness=float(data["nyt_likeness"]),
                clarity=float(data["clarity"]),
                ambiguity_risk=float(data["ambiguity_risk"]),
                solver_confidence=float(data["solver_confidence"]),
                would_publish=bool(data["would_publish"]),
                rationale=str(data["rationale"]),
                possible_alternative_groups=[str(item) for item in data["possible_alternative_groups"]],
                revision_suggestions=[str(item) for item in data["revision_suggestions"]],
            )
        )
    return results


def judge_puzzle(puzzle: Puzzle, provider: str = "offline", model: str | None = None) -> JudgeResult:
    if provider == "offline":
        return offline_judge(puzzle)
    if provider == "openai":
        return openai_judge(puzzle, model=model)
    raise ValueError(f"Unknown judge provider: {provider}")


def build_judge_prompt(puzzle: Puzzle) -> str:
    groups = "\n".join(
        f"- {group.category}: {', '.join(group.words)}. Explanation: {group.explanation}"
        for group in puzzle.groups
    )
    return f"""
Evaluate this candidate Connections puzzle.

Displayed words:
{', '.join(puzzle.words)}

Intended answer groups:
{groups}

Curator note:
{puzzle.curator_note}

Evaluation rules:
- Score NYT-likeness from 0 to 100.
- Score clarity from 0 to 100.
- Score ambiguity risk from 0 to 100, where higher means more dangerous.
- Score solver confidence from 0 to 100.
- would_publish should be true only if the puzzle is fair enough for manual review.
- List any plausible alternative groups if you see them.
- Suggest concrete revisions if the puzzle is weak.
"""


def build_batch_judge_prompt(puzzles: list[Puzzle]) -> str:
    blocks = []
    for puzzle in puzzles:
        groups = "\n".join(
            f"  - {group.category}: {', '.join(group.words)}. Explanation: {group.explanation}"
            for group in puzzle.groups
        )
        blocks.append(
            f"""
Puzzle ID: {puzzle.id}
Title: {puzzle.title}
Displayed words: {', '.join(puzzle.words)}
Intended answer groups:
{groups}
Curator note: {puzzle.curator_note}
"""
        )
    return f"""
Evaluate each candidate Connections puzzle below.

For each puzzle:
- Copy puzzle_id exactly.
- Score NYT-likeness from 0 to 100.
- Score clarity from 0 to 100.
- Score ambiguity risk from 0 to 100, where higher means more dangerous.
- Score solver confidence from 0 to 100.
- would_publish should be true only if the puzzle is fair enough for a reviewed bank.
- List plausible alternative groups if you see them.
- Suggest concrete revisions if the puzzle is weak.

Puzzles:
{''.join(blocks)}
"""
