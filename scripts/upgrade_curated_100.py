"""Rebuild the curated 100 puzzle bank using the v2 generator.

Strategy:

  1. Generate ~600 candidates in mixed mode (theme_first + template).
  2. Score each candidate with:
       - hard validator (schema + uniqueness + explanation),
       - blind solver uniqueness (existing pipeline),
       - light readability checks (category length, wordplay balance).
  3. Keep a diverse top-100 by greedy selection:
       - at most N duplicates of an exact answer group,
       - at most M reuses of any single word,
       - at most K reuses of any category name.
  4. Write to data/puzzles/curated_100_v2.json. The old curated_100.json
     is preserved for comparison; update web/app.js data loader to
     prefer the v2 file once we confirm quality.

Usage:

    python scripts/upgrade_curated_100.py --candidates 600 --seed 561

The script is deterministic given the seed.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from infinite_connections.generator_v2 import GeneratorV2  # noqa: E402
from infinite_connections.schema import Puzzle, normalize_word  # noqa: E402
from infinite_connections.solver import solve_puzzle  # noqa: E402
from infinite_connections.validator import score_puzzle  # noqa: E402


MAX_WORD_REUSE = 5
MAX_CATEGORY_REUSE = 4


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return path.name


def _eligible(puzzle: Puzzle) -> tuple[bool, list[str]]:
    """Hard filters applied before diversity selection."""
    reasons: list[str] = []
    report = score_puzzle(puzzle)
    if report.status == "reject":
        reasons.extend(report.rejection_reasons)
    solver_result = solve_puzzle(puzzle)
    if solver_result.status not in ("unique_match", "ambiguous_with_match"):
        reasons.append(f"blind_solver:{solver_result.status}")
    if solver_result.status == "ambiguous_with_match":
        reasons.append("blind_solver:ambiguous")
    return (not reasons, reasons)


def _score(puzzle: Puzzle) -> float:
    """Higher is better. Rewards wordplay + theme + difficulty spread."""
    strategies = {g.strategy for g in puzzle.groups}
    diversity = len(strategies)
    purples = sum(1 for g in puzzle.groups if g.difficulty == "purple")
    yellows = sum(1 for g in puzzle.groups if g.difficulty == "yellow")
    has_wordplay = any(g.strategy == "wordplay" for g in puzzle.groups)
    balanced_difficulty = 1.0 if (purples and yellows) else 0.5
    mean_category_len = sum(len(g.category or "") for g in puzzle.groups) / 4
    short_category_bonus = 1.0 if 8 <= mean_category_len <= 30 else 0.6
    return (
        0.35 * (1.0 if has_wordplay else 0.2)
        + 0.25 * (diversity / 4.0)
        + 0.20 * balanced_difficulty
        + 0.20 * short_category_bonus
    )


def select_diverse_top(
    puzzles: list[Puzzle], target: int = 100
) -> list[Puzzle]:
    puzzles = sorted(puzzles, key=_score, reverse=True)
    selected: list[Puzzle] = []
    exact_groups: set[tuple[str, ...]] = set()
    word_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()
    for puzzle in puzzles:
        signatures = [tuple(sorted(g.normalized_words())) for g in puzzle.groups]
        if any(sig in exact_groups for sig in signatures):
            continue
        if any(word_counts[w] >= MAX_WORD_REUSE for w in puzzle.normalized_words()):
            continue
        if any(category_counts[g.category] >= MAX_CATEGORY_REUSE for g in puzzle.groups):
            continue
        # Commit.
        for sig in signatures:
            exact_groups.add(sig)
        for w in puzzle.normalized_words():
            word_counts[w] += 1
        for g in puzzle.groups:
            category_counts[g.category] += 1
        selected.append(puzzle)
        if len(selected) >= target:
            break
    return selected


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", type=int, default=600)
    parser.add_argument("--seed", type=int, default=561)
    parser.add_argument("--out", default="data/puzzles/curated_100_v2.json")
    parser.add_argument("--mode", choices=["template", "theme_first", "mixed"],
                        default="mixed")
    parser.add_argument("--theme-prob", type=float, default=0.35,
                        help="only used when --mode=mixed")
    parser.add_argument("--no-rewrite", action="store_true",
                        help="skip Ollama category-name rewriting")
    parser.add_argument("--offline-themes", action="store_true",
                        help="use offline theme suggestions instead of Ollama")
    parser.add_argument("--skip-ollama", action="store_true",
                        help="force template mode and avoid all Ollama calls")
    args = parser.parse_args()

    mode = "template" if args.skip_ollama else args.mode
    print(f"Generating {args.candidates} candidates (mode={mode})...")
    gen = GeneratorV2(
        mode=mode,
        theme_first_probability=args.theme_prob,
        rewrite_categories_with_ollama=not args.no_rewrite,
        use_ollama=not args.offline_themes and not args.skip_ollama,
    )
    pool = gen.generate(count=args.candidates, seed=args.seed)

    eligible: list[Puzzle] = []
    rejected: list[tuple[str, list[str]]] = []
    for puzzle in pool:
        ok, reasons = _eligible(puzzle)
        if ok:
            eligible.append(puzzle)
        else:
            rejected.append((puzzle.id, reasons))
    print(f"Eligible after hard filters: {len(eligible)} / {len(pool)}")

    curated = select_diverse_top(eligible, target=100)

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = ROOT / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps([p.to_dict() for p in curated], indent=2), encoding="utf-8"
    )
    print(f"Wrote {len(curated)} puzzles -> {_display_path(out_path)}")

    rep_path = out_path.with_name(out_path.stem + "_rejections.json")
    rep_path.write_text(json.dumps(rejected, indent=2), encoding="utf-8")
    print(f"Rejection reasons -> {_display_path(rep_path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
