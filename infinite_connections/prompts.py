"""Prompt library for Ollama + external solver calls.

Prompts are kept here (not inline) so the evaluation pipeline is
reproducible: we can audit exactly what text went to every solver
and freeze version strings for the technical appendix.
"""

from __future__ import annotations

SOLVER_SYSTEM = (
    "You are an expert NYT Connections player. "
    "Given 16 words, partition them into exactly four groups of four "
    "based on a hidden category each group shares. "
    "Categories may be semantic ('types of fish'), phrase completion "
    "('words that can precede CARD'), wordplay (homophones, rhymes, "
    "anagrams, hidden words), or cultural references. "
    "Answer with ONLY valid JSON and no prose outside the JSON."
)

SOLVER_USER_TEMPLATE = """Here are 16 words:

{word_list}

Partition them into 4 groups of 4. Return JSON in exactly this schema:

{{
  "groups": [
    {{"category": "short label (<=8 words)", "words": ["W1","W2","W3","W4"]}},
    {{"category": "...", "words": ["..","..","..",".."]}},
    {{"category": "...", "words": ["..","..","..",".."]}},
    {{"category": "...", "words": ["..","..","..",".."]}}
  ]
}}

Rules:
- Every word in the input must appear in exactly one group.
- Do not invent words.
- Be concrete and specific in category names.
- Output ONLY the JSON object. No preface, no trailing text."""


THEME_SUGGESTER_SYSTEM = (
    "You are a puzzle editor designing a themed NYT Connections board. "
    "Propose a single, creative, non-obvious theme. "
    "Good themes tie four distinct word groups together under one subtle concept. "
    "Avoid generic themes like 'colors' or 'animals'. "
    "Output ONE short theme description in 3-8 words."
)

THEME_SUGGESTER_USER = (
    "Suggest a fresh, playful theme suitable for an NYT Connections puzzle. "
    "Examples of strong themes: 'compound words hiding a body part', "
    "'nicknames of U.S. presidents', 'phrases that can follow SNAKE', "
    "'animals that moonlight as tools', 'palindromic short words'. "
    "Return exactly one theme as a short phrase."
)


CATEGORY_NAMER_SYSTEM = (
    "You are a puzzle editor writing short, punchy category labels for an "
    "NYT Connections board. Labels should be 2-6 words, lowercase where "
    "appropriate, and capture what unifies the four words."
)

CATEGORY_NAMER_USER_TEMPLATE = """Write a single short category label for these four words:

{word_list}

They share this hidden structure: {mechanism_hint}

Return ONLY the label text (2-6 words). No quotes, no prose."""


CURATOR_NOTE_SYSTEM = (
    "You are a puzzle curator writing a one-sentence publication note. "
    "Describe the puzzle's character in a single concrete sentence - the "
    "tone, difficulty feel, or a subtle trick - without revealing answers."
)

CURATOR_NOTE_USER_TEMPLATE = """Puzzle groups (hidden from the solver):

{groups_summary}

Theme: {theme}

Write ONE curator note (1 sentence, 15-28 words) for this puzzle. Do not
mention specific answer words. Do not enumerate the categories. Just
capture the puzzle's feel."""


def build_solver_user_prompt(words: list[str]) -> str:
    """Render the solver prompt for a specific 16-word board."""
    word_list = "\n".join(f"- {word.upper()}" for word in words)
    return SOLVER_USER_TEMPLATE.format(word_list=word_list)


def build_category_namer_prompt(words: list[str], mechanism_hint: str) -> str:
    word_list = ", ".join(word.upper() for word in words)
    return CATEGORY_NAMER_USER_TEMPLATE.format(
        word_list=word_list,
        mechanism_hint=mechanism_hint,
    )


def build_curator_note_prompt(groups: list[dict], theme: str) -> str:
    lines = []
    for index, group in enumerate(groups, 1):
        category = group.get("category", f"group {index}")
        lines.append(f"{index}. {category} (strategy: {group.get('strategy', 'unknown')})")
    return CURATOR_NOTE_USER_TEMPLATE.format(
        groups_summary="\n".join(lines),
        theme=theme or "untitled",
    )
