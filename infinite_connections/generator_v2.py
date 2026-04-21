"""Unified v2 generator - combines legacy template mode + theme-first mode.

This is a strict superset of the v1 `LocalTemplateGenerator`:

  mode = "template"     -> legacy behaviour (kept for reproducibility of
                           the v1 10K stress tests)
  mode = "theme_first"  -> new theme-first pipeline (Ollama -> sub-angles
                           -> wordplay-enriched draws), falls back to
                           template mode when Ollama is unreachable
  mode = "mixed"        -> for every puzzle, flip a weighted coin to
                           pick mode per puzzle (default: 0.6 theme_first
                           / 0.4 template)

The constructor never raises on missing Ollama; the generator downgrades
gracefully so cached batches are deterministic and reproducible on any
machine.
"""

from __future__ import annotations

import hashlib
import random
from typing import Iterable, Literal

from .config import CONFIG
from .generator import (
    LocalTemplateGenerator,
    build_curator_note,
    build_decoy_notes,
    build_image_prompt,
    infer_theme,
    neutral_title,
)
from .ollama_client import OllamaClient, OllamaError
from .schema import Puzzle, PuzzleGroup
from .seed_bank import CategoryTemplate, CATEGORY_BANK
from .theme_generator import (
    ThemeFirstGenerator,
    ThemedBoard,
    rewrite_category_via_ollama,
)
from .wordplay import (
    WordplayGroup,
    enumerate_wordplay_groups,
    letter_homophone_group,
)


GeneratorMode = Literal["template", "theme_first", "mixed"]


class GeneratorV2:
    """Top-level generator that hides which sub-mode produced each puzzle."""

    def __init__(
        self,
        *,
        mode: GeneratorMode = "mixed",
        theme_first_probability: float = 0.6,
        ollama_host: str | None = None,
        ollama_model: str | None = None,
        categories: Iterable[CategoryTemplate] = CATEGORY_BANK,
        rewrite_categories_with_ollama: bool = True,
        use_ollama: bool = True,
    ) -> None:
        self.mode = mode
        self.theme_first_probability = theme_first_probability
        self.categories = tuple(categories)
        self._template_generator = LocalTemplateGenerator(self.categories)

        host = ollama_host or CONFIG.ollama_host
        model = ollama_model or CONFIG.ollama_generator.name
        self.ollama = OllamaClient(host=host) if host and use_ollama else None
        self.ollama_model = model
        self.rewrite_categories_with_ollama = rewrite_categories_with_ollama

        self._ollama_healthy: bool | None = None
        self._theme_generator = ThemeFirstGenerator(
            ollama=self.ollama,
            generator_model=self.ollama_model,
            category_bank=self.categories,
        )
        # Pre-compute wordplay pool once. This is deterministic given the
        # seed bank so every generator instance shares the same structured
        # pool; generation randomness comes from per-puzzle sampling.
        dictionary = _collect_dictionary(self.categories)
        self._wordplay_pool: list[WordplayGroup] = enumerate_wordplay_groups(
            dictionary, rng=random.Random(561)
        )
        # Pad with a letter-homophone group (only one, by construction).
        letter_group = letter_homophone_group(random.Random(562))
        if letter_group:
            self._wordplay_pool.append(letter_group)

    # ── Public API ──────────────────────────────────────────────

    def generate(self, count: int, seed: int | None = None) -> list[Puzzle]:
        rng = random.Random(seed)
        results: list[Puzzle] = []
        attempt = 0
        while len(results) < count and attempt < count * 40:
            attempt += 1
            mode = self._pick_mode(rng)
            if mode == "theme_first":
                puzzle = self._generate_theme_first(rng, index=len(results))
                if puzzle is not None:
                    results.append(puzzle)
                    continue
                # Fall through to template mode on failure.
            puzzle = self._generate_template(rng, index=len(results))
            if puzzle is not None:
                results.append(puzzle)
        return results

    # ── Internals ───────────────────────────────────────────────

    def _pick_mode(self, rng: random.Random) -> str:
        if self.mode == "template":
            return "template"
        if self.mode == "theme_first":
            return "theme_first"
        return "theme_first" if rng.random() < self.theme_first_probability else "template"

    def _ollama_available(self) -> bool:
        if self._ollama_healthy is None:
            if not self.ollama:
                self._ollama_healthy = False
            else:
                try:
                    self._ollama_healthy = self.ollama.health()
                except OllamaError:
                    self._ollama_healthy = False
        return self._ollama_healthy

    def _generate_template(self, rng: random.Random, *, index: int) -> Puzzle | None:
        puzzles = self._template_generator.generate(1, seed=rng.randint(0, 10_000_000))
        return puzzles[0] if puzzles else None

    def _generate_theme_first(self, rng: random.Random, *, index: int) -> Puzzle | None:
        board = self._theme_generator.compose(rng=rng, wordplay_pool=self._wordplay_pool)
        if board is None:
            return None

        # Optional: rewrite category names with Ollama for a NYT-ish feel.
        categories = list(board.group_categories)
        if self.rewrite_categories_with_ollama and self._ollama_available() and self.ollama:
            for i in range(4):
                better = rewrite_category_via_ollama(
                    self.ollama,
                    self.ollama_model,
                    words=board.groups[i],
                    mechanism_hint=f"{board.group_strategies[i]} (theme: {board.theme})",
                )
                if better:
                    categories[i] = better

        all_words = board.flat_words()
        digest = hashlib.sha1(("|".join(all_words) + str(index)).encode("utf-8")).hexdigest()[:10]
        shuffled = list(all_words)
        random.Random(digest).shuffle(shuffled)

        groups = [
            PuzzleGroup(
                id=f"g{i + 1}",
                category=categories[i],
                words=list(board.groups[i]),
                difficulty=board.group_difficulties[i],
                strategy=board.group_strategies[i],
                explanation=board.explanations[i],
            )
            for i in range(4)
        ]
        strategies = sorted({g.strategy for g in groups})
        return Puzzle(
            id=f"tfv2-{digest}",
            title=neutral_title(index + 1),
            theme=board.theme,
            words=shuffled,
            groups=groups,
            source_strategy="+".join(strategies),
            curator_note=_compose_theme_note(board),
            decoy_notes=_theme_decoy_notes(board),
            image_prompt=build_image_prompt(board.theme),
            metadata={
                "generator": "GeneratorV2.theme_first",
                "theme": board.theme,
                "mechanism_mix": [angle.mechanism for angle in board.sub_angles],
                "groups": [g.to_dict() for g in groups],
            },
        )


# ── Helpers ─────────────────────────────────────────────────────


def _collect_dictionary(categories: Iterable[CategoryTemplate]) -> set[str]:
    """Union of all words appearing in the seed bank."""
    words: set[str] = set()
    for template in categories:
        for word in template.words:
            words.add(word.upper())
    return words


def _compose_theme_note(board: ThemedBoard) -> str:
    """Short curator note that actually varies per puzzle."""
    mechs = ", ".join(sorted({angle.mechanism.replace("_", " ") for angle in board.sub_angles}))
    return (
        f"Theme: {board.theme}. "
        f"Mechanics in play: {mechs}. "
        "Answers stay hidden during normal play."
    )


def _theme_decoy_notes(board: ThemedBoard) -> list[str]:
    notes: list[str] = []
    if any(angle.mechanism == "wordplay" for angle in board.sub_angles):
        notes.append("One group is a wordplay trap - check sound and spelling.")
    if sum(1 for a in board.sub_angles if a.mechanism == "phrase_completion") >= 2:
        notes.append("Two phrase-completion groups share surface similarity; solver agreement should be checked.")
    return notes
