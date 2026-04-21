"""Audit a generated puzzle batch for scale, diversity, and exact NYT overlap.

This is the fast, deterministic experiment we can cite before running
expensive multi-solver judges.  It checks the failure modes the instructor
explicitly called out:

  * malformed puzzles,
  * repeated boards or repeated exact answer groups,
  * accidental reproduction of a historical NYT board,
  * blind-solver uniqueness on a deterministic sample.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from infinite_connections.schema import Puzzle  # noqa: E402
from infinite_connections.solver import solve_puzzle  # noqa: E402
from infinite_connections.validator import validate_puzzle  # noqa: E402


def _load_items(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, list) else payload.get("puzzles", [])


def _signature(words: list[str]) -> tuple[str, ...]:
    return tuple(sorted(str(word).strip().upper() for word in words))


def _history_signatures(path: Path) -> set[tuple[str, ...]]:
    if not path.exists():
        return set()
    items = _load_items(path)
    return {_signature(item.get("words", [])) for item in items if len(item.get("words", [])) == 16}


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return path.name


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--history", default="data/history/unified_reference.json")
    parser.add_argument("--out", required=True)
    parser.add_argument("--validate-sample", type=int, default=1000)
    parser.add_argument("--blind-sample", type=int, default=500)
    parser.add_argument("--max-solutions", type=int, default=25)
    args = parser.parse_args()

    input_path = Path(args.input) if Path(args.input).is_absolute() else ROOT / args.input
    history_path = Path(args.history) if Path(args.history).is_absolute() else ROOT / args.history
    out_path = Path(args.out) if Path(args.out).is_absolute() else ROOT / args.out

    raw_items = _load_items(input_path)
    puzzles: list[Puzzle] = []
    malformed = 0
    for item in raw_items:
        try:
            puzzles.append(Puzzle.from_dict(item))
        except Exception:
            malformed += 1

    board_counts: Counter[tuple[str, ...]] = Counter()
    group_counts: Counter[tuple[str, ...]] = Counter()
    word_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()
    strategy_counts: Counter[str] = Counter()
    validation_errors: list[dict[str, str]] = []

    for puzzle in puzzles:
        board_counts[_signature(puzzle.normalized_words())] += 1
        word_counts.update(puzzle.normalized_words())
        strategy_counts[puzzle.source_strategy] += 1
        for group in puzzle.groups:
            group_counts[_signature(group.normalized_words())] += 1
            category_counts[group.category] += 1

    for puzzle in puzzles[: max(0, args.validate_sample)]:
        for issue in validate_puzzle(puzzle):
            if issue.severity == "error":
                validation_errors.append({
                    "puzzle_id": puzzle.id,
                    "code": issue.code,
                    "message": issue.message,
                })

    history = _history_signatures(history_path)
    exact_history_overlaps = [
        puzzle.id for puzzle in puzzles if _signature(puzzle.normalized_words()) in history
    ]

    solver_status: Counter[str] = Counter()
    solver_examples: list[dict[str, Any]] = []
    for puzzle in puzzles[: max(0, args.blind_sample)]:
        result = solve_puzzle(puzzle, max_solutions=args.max_solutions)
        solver_status[result.status] += 1
        if result.status != "unique_match" and len(solver_examples) < 20:
            solver_examples.append(result.to_dict())

    blind_checked = min(len(puzzles), max(0, args.blind_sample))
    payload: dict[str, Any] = {
        "input": _display_path(input_path),
        "history": _display_path(history_path),
        "count": len(puzzles),
        "malformed": malformed,
        "unique_boards": len(board_counts),
        "duplicate_board_slots": sum(c - 1 for c in board_counts.values() if c > 1),
        "unique_exact_groups": len(group_counts),
        "duplicate_exact_group_slots": sum(c - 1 for c in group_counts.values() if c > 1),
        "unique_words": len(word_counts),
        "max_word_count": max(word_counts.values(), default=0),
        "max_group_count": max(group_counts.values(), default=0),
        "max_category_count": max(category_counts.values(), default=0),
        "strategy_counts": dict(strategy_counts),
        "top_words": word_counts.most_common(30),
        "top_groups": [
            {"count": count, "words": list(signature)}
            for signature, count in group_counts.most_common(30)
        ],
        "top_categories": category_counts.most_common(30),
        "validation_sample": {
            "checked": min(len(puzzles), max(0, args.validate_sample)),
            "error_count": len(validation_errors),
            "errors": validation_errors[:20],
        },
        "history_overlap": {
            "history_count": len(history),
            "exact_overlap_count": len(exact_history_overlaps),
            "examples": exact_history_overlaps[:20],
        },
        "blind_solver_sample": {
            "checked": blind_checked,
            "status_counts": dict(solver_status),
            "unique_match": solver_status["unique_match"],
            "unique_match_rate": round(
                solver_status["unique_match"] / blind_checked, 4
            ) if blind_checked else 0.0,
            "examples": solver_examples,
        },
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Audited {len(puzzles)} puzzles from {_display_path(input_path)}")
    print(f"Exact historical overlaps: {payload['history_overlap']['exact_overlap_count']}")
    print(f"Blind unique-match rate: {payload['blind_solver_sample']['unique_match_rate']}")
    print(f"Wrote {_display_path(out_path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
