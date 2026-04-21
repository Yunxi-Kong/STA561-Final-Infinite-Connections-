"""Candidate puzzle generators."""

from __future__ import annotations

import hashlib
import json
import os
import random
from dataclasses import asdict
from typing import Protocol

from .schema import PUZZLE_JSON_SCHEMA, Puzzle, PuzzleGroup
from .seed_bank import CATEGORY_BANK, CategoryTemplate


class PuzzleGenerator(Protocol):
    def generate(self, count: int, seed: int | None = None) -> list[Puzzle]:
        """Return candidate puzzles."""


class LocalTemplateGenerator:
    """Deterministic generator for offline development and reproducibility."""

    def __init__(self, categories: tuple[CategoryTemplate, ...] = CATEGORY_BANK) -> None:
        self.categories = tuple(categories)
        self.sample_size = min(len(self.categories), 360)

    def generate(self, count: int, seed: int | None = None) -> list[Puzzle]:
        rng = random.Random(seed)
        puzzles: list[Puzzle] = []
        attempts = 0
        seen_signatures: set[tuple[str, ...]] = set()
        while len(puzzles) < count and attempts < count * 80:
            attempts += 1
            templates = self.draw_templates(rng)
            selected: list[CategoryTemplate] = []
            used_words: set[str] = set()
            for template in templates:
                words = set(template.words)
                if words & used_words:
                    continue
                if not can_add_template(selected, template):
                    continue
                selected.append(template)
                used_words.update(words)
                if len(selected) == 4:
                    break
            if len(selected) != 4:
                continue
            signature = tuple(sorted(word for template in selected for word in template.words))
            if signature in seen_signatures:
                continue
            title = neutral_title(len(puzzles) + 1)
            puzzle = build_puzzle(selected, title=title, salt=f"{seed}-{attempts}")
            seen_signatures.add(signature)
            puzzles.append(puzzle)
        return puzzles

    def draw_templates(self, rng: random.Random) -> list[CategoryTemplate]:
        if self.sample_size >= len(self.categories):
            templates = list(self.categories)
            rng.shuffle(templates)
            return templates
        return rng.sample(self.categories, self.sample_size)


class OpenAIStructuredGenerator:
    """Optional OpenAI-backed generator using structured JSON outputs."""

    def __init__(self, model: str | None = None) -> None:
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5.4-mini")

    def generate(self, count: int, seed: int | None = None) -> list[Puzzle]:
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("Install optional dependencies with `python -m pip install -r requirements.txt`.") from exc
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("Set OPENAI_API_KEY before using --provider openai.")

        client = OpenAI()
        puzzles: list[Puzzle] = []
        for index in range(count):
            response = client.responses.create(  # pragma: no cover - live API path
                model=self.model,
                input=[
                    {"role": "system", "content": "You are a careful NYT Connections-style puzzle editor."},
                    {"role": "user", "content": build_openai_prompt(seed=seed, index=index)},
                ],
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "connection_puzzle",
                        "schema": PUZZLE_JSON_SCHEMA,
                        "strict": True,
                    }
                },
            )
            puzzles.append(Puzzle.from_dict(json.loads(response.output_text)))
        return puzzles


def build_puzzle(templates: list[CategoryTemplate], title: str, salt: str) -> Puzzle:
    words = [word for template in templates for word in template.words]
    digest = hashlib.sha1(("|".join(words) + salt).encode("utf-8")).hexdigest()[:10]
    groups = [
        PuzzleGroup(
            id=f"g{index + 1}",
            category=template.category,
            words=list(template.words),
            difficulty=template.difficulty,
            strategy=template.strategy,
            explanation=template.explanation,
        )
        for index, template in enumerate(templates)
    ]
    shuffled_words = list(words)
    random.Random(digest).shuffle(shuffled_words)
    strategies = sorted({template.strategy for template in templates})
    return Puzzle(
        id=f"local-{digest}",
        title=title,
        theme=infer_theme(templates),
        words=shuffled_words,
        groups=groups,
        source_strategy="+".join(strategies),
        curator_note=build_curator_note(title, templates),
        decoy_notes=build_decoy_notes(templates),
        image_prompt=build_image_prompt(title),
        metadata={"generator": "LocalTemplateGenerator", "templates": [asdict(template) for template in templates]},
    )


def can_add_template(selected: list[CategoryTemplate], candidate: CategoryTemplate) -> bool:
    strategies = [template.strategy for template in selected]
    if any(template.category == candidate.category for template in selected):
        return False
    if candidate.strategy == "phrase_completion" and strategies.count("phrase_completion") >= 2:
        return False
    if candidate.strategy == "wordplay" and strategies.count("wordplay") >= 1:
        return False
    candidate_domain = template_domain(candidate)
    if candidate_domain and any(template_domain(template) == candidate_domain for template in selected):
        return False
    return True


def template_domain(template: CategoryTemplate) -> str:
    category = template.category.upper()
    if any(token in category for token in ("TEA", "PASTA", "CAKE", "BREAKFAST", "BAKERY")):
        return "food"
    if any(token in category for token in ("KEYBOARD", "BROWSER", "COMPUTER", "PHONE", "SOFTWARE", "CYBER", "PROGRAMMING", "EMAIL", "DATA")):
        return "interface"
    if any(token in category for token in ("THEATER", "MUSICAL", "AUDIO")):
        return "stage_audio"
    if any(token in category for token in ("SCHOOL", "SCIENTIFIC", "MATH", "LAB", "CHEMICAL", "MEASUREMENT")):
        return "academic_science"
    if any(token in category for token in ("COUNTRIES", "CITIES", "RIVERS", "MOUNTAIN", "ISLAND", "SEAS", "OCEANS", "STATES", "CAPITALS")):
        return "geography"
    if any(token in category for token in ("CARD", "BOARD", "CASINO", "CHESS", "PLAYING")):
        return "games"
    if any(token in category for token in ("BODY", "ORGANS", "BONES", "MEDICAL", "SPA")):
        return "health_body"
    if any(token in category for token in ("TRACK", "SWIMMING", "TENNIS", "BASEBALL", "BASKETBALL", "SOCCER", "GOLF")):
        return "sports"
    if any(token in category for token in ("MUSIC", "INSTRUMENTS", "VOICE", "DANCE")):
        return "music_performance"
    return ""


def infer_theme(templates: list[CategoryTemplate]) -> str:
    strategies = {template.strategy for template in templates}
    if "wordplay" in strategies and "phrase_completion" in strategies:
        return "language traps and familiar phrases"
    if "phrase_completion" in strategies:
        return "compound phrases"
    return "everyday categories"


def build_curator_note(title: str, templates: list[CategoryTemplate]) -> str:
    category_names = ", ".join(template.category for template in templates)
    return (
        f"{title} contains four compact groups: {category_names}. "
        "The board is designed to be playable first, with the answer structure available in Review mode."
    )


def build_decoy_notes(templates: list[CategoryTemplate]) -> list[str]:
    notes: list[str] = []
    strategies = [template.strategy for template in templates]
    if strategies.count("phrase_completion") >= 2:
        notes.append("Multiple phrase-completion groups create surface similarity, so solver agreement should be checked before publication.")
    if any(template.difficulty == "purple" for template in templates):
        notes.append("A purple group is present; ambiguity checks should be stricter than for direct semantic categories.")
    return notes


def build_image_prompt(title: str) -> str:
    return (
        "A refined editorial background for a word puzzle web app, "
        f"theme title '{title}', subtle paper texture, soft gallery lighting, "
        "minimal abstract letterforms, no readable text, no logos."
    )


def neutral_title(index: int) -> str:
    return f"Puzzle {index:03d}"


def build_openai_prompt(seed: int | None, index: int) -> str:
    return f"""
Create one original NYT Connections-style puzzle. Do not copy any past puzzle.

Requirements:
- Exactly 16 unique common English words.
- Exactly 4 answer groups of 4 words.
- Include a mix of semantic categories and phrase-completion categories.
- Include at most one risky wordplay group.
- Prefer fair, human-solvable categories over obscure trivia.
- Write concise explanations.
- Add notes about possible decoys or ambiguity.
- Return only JSON matching the provided schema.

Seed: {seed}
Candidate index: {index}
"""
