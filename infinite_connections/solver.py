"""Offline blind solver for ambiguity checks.

The solver only sees the 16 displayed words and the local answer-bank index.
It does not read puzzle explanations or judge rationales.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
import random
from typing import Iterable

from .schema import Puzzle, normalize_word
from .seed_bank import CATEGORY_BANK, CategoryTemplate
from .wordplay import enumerate_wordplay_groups, letter_homophone_group


@dataclass(frozen=True, slots=True)
class SolverGroup:
    signature: tuple[str, str, str, str]
    category: str
    strategy: str
    difficulty: str
    mask: int

    def to_dict(self) -> dict:
        return {
            "words": list(self.signature),
            "category": self.category,
            "strategy": self.strategy,
            "difficulty": self.difficulty,
        }


@dataclass(frozen=True, slots=True)
class SolverResult:
    puzzle_id: str
    status: str
    candidate_group_count: int
    solution_count: int
    intended_solution_found: bool
    ambiguity_score: float
    extra_candidate_groups: list[SolverGroup]
    solutions: list[list[SolverGroup]]

    def to_dict(self) -> dict:
        return {
            "puzzle_id": self.puzzle_id,
            "status": self.status,
            "candidate_group_count": self.candidate_group_count,
            "solution_count": self.solution_count,
            "intended_solution_found": self.intended_solution_found,
            "ambiguity_score": round(self.ambiguity_score, 2),
            "extra_candidate_groups": [group.to_dict() for group in self.extra_candidate_groups],
            "solutions": [[group.to_dict() for group in solution] for solution in self.solutions],
        }


def _build_answer_group_index() -> dict[tuple[str, ...], CategoryTemplate]:
    """Seed-bank plus deterministic generated wordplay groups.

    The v2 generator can draw wordplay groups from CMU/WordNet-derived
    mechanisms, not only from static CategoryTemplate rows.  The blind
    solver should know those same mechanisms; otherwise it falsely reports
    "no exact cover" for valid generated wordplay boards.
    """
    index = {tuple(sorted(template.words)): template for template in CATEGORY_BANK}
    dictionary = {word.upper() for template in CATEGORY_BANK for word in template.words}
    generated = enumerate_wordplay_groups(dictionary, rng=random.Random(561))
    letter_group = letter_homophone_group(random.Random(562))
    if letter_group:
        generated.append(letter_group)
    for group in generated:
        if len(group.words) != 4:
            continue
        signature = tuple(sorted(word.upper() for word in group.words))
        index.setdefault(
            signature,
            CategoryTemplate(
                category=group.category,
                words=tuple(word.upper() for word in group.words),  # type: ignore[arg-type]
                difficulty=group.difficulty,
                strategy="wordplay",
                explanation=group.explanation,
            ),
        )
    return index


ANSWER_GROUP_INDEX: dict[tuple[str, ...], CategoryTemplate] = _build_answer_group_index()


def solve_puzzle(puzzle: Puzzle, max_solutions: int = 25) -> SolverResult:
    board_words = sorted({normalize_word(word) for word in puzzle.words})
    word_to_bit = {word: 1 << index for index, word in enumerate(board_words)}
    full_mask = (1 << len(board_words)) - 1
    candidates = candidate_groups(board_words, word_to_bit)
    intended = intended_signatures(puzzle)
    solutions = enumerate_solutions(candidates, full_mask, max_solutions=max_solutions)
    solution_signatures = [{group.signature for group in solution} for solution in solutions]
    intended_found = intended in solution_signatures
    extra = [group for group in candidates if group.signature not in intended]
    status = solver_status(solutions, intended_found, max_solutions)
    ambiguity = ambiguity_score(status, len(extra), len(solutions), max_solutions)
    return SolverResult(
        puzzle_id=puzzle.id,
        status=status,
        candidate_group_count=len(candidates),
        solution_count=len(solutions),
        intended_solution_found=intended_found,
        ambiguity_score=ambiguity,
        extra_candidate_groups=extra[:12],
        solutions=solutions[: min(max_solutions, 5)],
    )


def candidate_groups(board_words: list[str], word_to_bit: dict[str, int]) -> list[SolverGroup]:
    candidates: list[SolverGroup] = []
    for combo in combinations(board_words, 4):
        signature = tuple(sorted(combo))
        template = ANSWER_GROUP_INDEX.get(signature)
        if template is None:
            continue
        mask = 0
        for word in signature:
            mask |= word_to_bit[word]
        candidates.append(
            SolverGroup(
                signature=signature,
                category=template.category,
                strategy=template.strategy,
                difficulty=template.difficulty,
                mask=mask,
            )
        )
    candidates.sort(key=lambda group: (group.strategy != "semantic", group.category, group.signature))
    return candidates


def enumerate_solutions(candidates: list[SolverGroup], full_mask: int, max_solutions: int) -> list[list[SolverGroup]]:
    by_bit: dict[int, list[SolverGroup]] = {}
    for group in candidates:
        mask = group.mask
        bit = 1
        while bit <= full_mask:
            if mask & bit:
                by_bit.setdefault(bit, []).append(group)
            bit <<= 1

    solutions: list[list[SolverGroup]] = []

    def search(remaining: int, chosen: list[SolverGroup]) -> None:
        if len(solutions) >= max_solutions:
            return
        if remaining == 0:
            if len(chosen) == 4:
                solutions.append(list(chosen))
            return
        if len(chosen) >= 4:
            return
        first_bit = remaining & -remaining
        for group in by_bit.get(first_bit, []):
            if group.mask & remaining != group.mask:
                continue
            chosen.append(group)
            search(remaining ^ group.mask, chosen)
            chosen.pop()

    search(full_mask, [])
    return solutions


def intended_signatures(puzzle: Puzzle) -> set[tuple[str, str, str, str]]:
    return {tuple(sorted(group.normalized_words())) for group in puzzle.groups}


def solver_status(solutions: list[list[SolverGroup]], intended_found: bool, max_solutions: int) -> str:
    if not solutions:
        return "no_exact_cover"
    if not intended_found:
        return "solver_disagrees"
    if len(solutions) >= max_solutions:
        return "many_solutions"
    if len(solutions) == 1:
        return "unique_match"
    return "ambiguous_with_match"


def ambiguity_score(status: str, extra_group_count: int, solution_count: int, max_solutions: int) -> float:
    if status == "unique_match":
        return min(20.0, extra_group_count * 1.5)
    if status == "ambiguous_with_match":
        return min(80.0, 25.0 + 12.0 * max(0, solution_count - 1) + extra_group_count * 2.0)
    if status == "many_solutions":
        return 90.0
    if status == "solver_disagrees":
        return 95.0
    return 100.0


def summarize_results(results: Iterable[SolverResult]) -> dict:
    rows = list(results)
    status_counts: dict[str, int] = {}
    for result in rows:
        status_counts[result.status] = status_counts.get(result.status, 0) + 1
    passed = sum(1 for result in rows if result.status == "unique_match")
    return {
        "count": len(rows),
        "unique_match": passed,
        "unique_match_rate": round(passed / len(rows), 3) if rows else 0.0,
        "status_counts": status_counts,
        "average_candidate_groups": round(sum(result.candidate_group_count for result in rows) / len(rows), 2) if rows else 0.0,
        "average_ambiguity_score": round(sum(result.ambiguity_score for result in rows) / len(rows), 2) if rows else 0.0,
    }
