"""Theme-first puzzle composer.

Real NYT Connections boards often have a soft overarching concept - the
four groups each relate to a shared theme (e.g. a single colour, a pop
culture figure, a cooking verb). Our v1 generator produced boards where
the four categories were unrelated; that was the single strongest
giveaway that a puzzle was AI-slop.

This module builds boards theme-first:

  1. Pick a theme (Ollama or a curated pool).
  2. Expand the theme into 4 candidate sub-angles with distinct mechanics
     (pure semantic, phrase completion, wordplay, cultural).
  3. For each sub-angle, draw a compatible 4-word group from:
       - the existing CategoryTemplate seed bank,
       - our CMU/WordNet-grounded wordplay generators, or
       - an Ollama brainstorm (last resort, guarded by a validator).
  4. Validate the combined board (16 unique words, blind-solver unique,
     no historical-NYT duplicates).

The generator does NOT depend on the user having Cerebras/Groq/Gemini
keys. Ollama is optional; when it's unreachable, we fall back to a
curated offline theme pool so offline reproducibility is preserved.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable, Iterable

from .ollama_client import ChatMessage, OllamaClient, OllamaError, parse_json_relaxed
from .prompts import (
    THEME_SUGGESTER_SYSTEM,
    THEME_SUGGESTER_USER,
    CATEGORY_NAMER_SYSTEM,
    build_category_namer_prompt,
)
from .seed_bank import CategoryTemplate, CATEGORY_BANK


# ── Offline theme pool (used when Ollama is unreachable) ────────

OFFLINE_THEME_POOL: tuple[str, ...] = (
    "words that change meaning across professions",
    "everyday objects that hide an animal name",
    "things you can open",
    "roles that moonlight as verbs",
    "phrases that complete a common expression with 'TIME'",
    "compound words involving a body part",
    "words that sound like letter names",
    "shared features of classic board games",
    "words that can follow 'WATER'",
    "US state words that are also ordinary nouns",
    "cooking actions disguised as other verbs",
    "musical words that exist outside music",
    "quiet words - small, cozy, subtle",
    "loud words - bold, abrupt, brash",
    "transportation without wheels",
    "palette of 'BLUE' in English idioms",
    "palette of 'GREEN' in English idioms",
    "nicknames that double as nouns",
    "cryptic words for surprise",
    "cryptic words for agreement",
    "terms in a legal thriller",
    "terms in a sci-fi cockpit",
    "palette of softness - downy, plush, velvet",
    "small mythical creatures",
    "computer terms that existed before computers",
    "weather words as moods",
    "compound words involving 'HAND'",
    "compound words involving 'HEAD'",
    "synonyms for CLUE",
    "synonyms for TRICK",
)


# ── Data classes ───────────────────────────────────────────────


@dataclass(slots=True)
class SubAngle:
    """One sub-angle within a theme, aligned to a mechanism bucket."""

    mechanism: str          # "semantic" | "phrase_completion" | "wordplay" | "cultural"
    description: str        # short hint for a human / LLM
    category_name: str = ""  # filled once the group is chosen


@dataclass(slots=True)
class ThemedBoard:
    """A themed puzzle board ready for downstream validation."""

    theme: str
    sub_angles: list[SubAngle]
    groups: list[list[str]]          # 4 lists of 4 words (upper-case)
    group_strategies: list[str]      # "semantic" | "phrase_completion" | "wordplay" | ...
    group_difficulties: list[str]    # "yellow" | "green" | "blue" | "purple"
    group_categories: list[str]
    explanations: list[str]

    def flat_words(self) -> list[str]:
        return [w for g in self.groups for w in g]


# ── Theme composer ─────────────────────────────────────────────


class ThemeFirstGenerator:
    """Produce themed 4x4 boards using Ollama when available."""

    def __init__(
        self,
        ollama: OllamaClient | None = None,
        generator_model: str | None = None,
        category_bank: Iterable[CategoryTemplate] | None = None,
    ) -> None:
        self.ollama = ollama
        self.generator_model = generator_model
        self.category_bank = tuple(category_bank or CATEGORY_BANK)
        # Index templates by strategy for quick sub-angle lookup.
        self._by_strategy: dict[str, list[CategoryTemplate]] = {}
        for template in self.category_bank:
            self._by_strategy.setdefault(template.strategy, []).append(template)

    # ── Public API ──────────────────────────────────────────────

    def suggest_theme(self, rng: random.Random) -> str:
        """Return a theme string. Try Ollama first, fall back to offline pool."""
        if self.ollama and self.generator_model:
            try:
                response = self.ollama.chat(
                    model=self.generator_model,
                    messages=[
                        ChatMessage(role="system", content=THEME_SUGGESTER_SYSTEM),
                        ChatMessage(role="user", content=THEME_SUGGESTER_USER),
                    ],
                    temperature=0.9,
                    max_tokens=60,
                    retries=1,
                )
                candidate = response.content.strip().strip('"').strip("'")
                # Take only the first line; some small models pad with prose.
                first_line = candidate.split("\n")[0].strip()
                if 3 <= len(first_line.split()) <= 15:
                    return first_line
            except OllamaError:
                pass
        return rng.choice(OFFLINE_THEME_POOL)

    def plan_sub_angles(self, theme: str, rng: random.Random) -> list[SubAngle]:
        """Fix a mechanism mix per board (variety is what makes it NYT-ish)."""
        recipes: list[list[str]] = [
            ["semantic", "semantic", "phrase_completion", "wordplay"],
            ["semantic", "phrase_completion", "phrase_completion", "wordplay"],
            ["semantic", "semantic", "semantic", "wordplay"],
            ["semantic", "phrase_completion", "wordplay", "wordplay"],
        ]
        recipe = rng.choice(recipes)
        return [
            SubAngle(mechanism=m, description=f"{m} angle of '{theme}'")
            for m in recipe
        ]

    def pick_group_for_angle(
        self,
        angle: SubAngle,
        used_words: set[str],
        rng: random.Random,
        wordplay_pool: list | None = None,
    ) -> tuple[list[str], str, str, str] | None:
        """Return (words, category_name, strategy, difficulty) or None."""
        mechanism = angle.mechanism
        if mechanism == "wordplay" and wordplay_pool:
            # The wordplay pool is a precomputed list of WordplayGroup.
            shuffled = list(wordplay_pool)
            rng.shuffle(shuffled)
            for item in shuffled:
                words = list(item.words)
                if any(w in used_words for w in words):
                    continue
                return (words, item.category, "wordplay", item.difficulty)
            return None

        # Default path: sample from the seed bank filtered by strategy.
        target_strategy = mechanism if mechanism in self._by_strategy else "semantic"
        pool = self._by_strategy.get(target_strategy, [])
        if not pool:
            return None
        shuffled = list(pool)
        rng.shuffle(shuffled)
        for template in shuffled:
            words = list(template.words)
            if any(w in used_words for w in words):
                continue
            return (words, template.category, template.strategy, template.difficulty)
        return None

    def compose(
        self,
        *,
        rng: random.Random,
        wordplay_pool: list | None = None,
        max_tries: int = 8,
    ) -> ThemedBoard | None:
        """One theme + 4 sub-angles -> one board; None if unable to fill."""
        for _ in range(max_tries):
            theme = self.suggest_theme(rng)
            sub_angles = self.plan_sub_angles(theme, rng)

            groups: list[list[str]] = []
            strategies: list[str] = []
            difficulties: list[str] = []
            categories: list[str] = []
            explanations: list[str] = []
            used: set[str] = set()

            ok = True
            for angle in sub_angles:
                outcome = self.pick_group_for_angle(angle, used, rng, wordplay_pool)
                if outcome is None:
                    ok = False
                    break
                words, cat, strategy, difficulty = outcome
                groups.append(words)
                strategies.append(strategy)
                difficulties.append(difficulty)
                categories.append(cat)
                explanations.append(_explain_group(strategy, cat))
                for w in words:
                    used.add(w)

            if ok and len(used) == 16:
                return ThemedBoard(
                    theme=theme,
                    sub_angles=sub_angles,
                    groups=groups,
                    group_strategies=strategies,
                    group_difficulties=difficulties,
                    group_categories=categories,
                    explanations=explanations,
                )
        return None


# ── Helpers ─────────────────────────────────────────────────────


def _explain_group(strategy: str, category: str) -> str:
    if strategy == "wordplay":
        return f"Wordplay: {category}."
    if strategy == "phrase_completion":
        return f"Each word forms a common compound with the shared pivot in '{category}'."
    return f"Each word is a {category.lower()} - a familiar semantic class."


def rewrite_category_via_ollama(
    ollama: OllamaClient, model: str, words: list[str], mechanism_hint: str
) -> str | None:
    """Ask Ollama for a crisper category label. Returns None on failure."""
    try:
        response = ollama.chat(
            model=model,
            messages=[
                ChatMessage(role="system", content=CATEGORY_NAMER_SYSTEM),
                ChatMessage(role="user", content=build_category_namer_prompt(words, mechanism_hint)),
            ],
            temperature=0.7,
            max_tokens=40,
            retries=1,
        )
    except OllamaError:
        return None
    text = response.content.strip().strip('"').strip("'").split("\n")[0].strip()
    if not text or len(text.split()) > 10:
        return None
    return text
