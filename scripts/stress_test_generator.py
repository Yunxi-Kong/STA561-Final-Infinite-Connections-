from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from infinite_connections.generator import LocalTemplateGenerator
from infinite_connections.seed_bank import CATEGORY_BANK
from infinite_connections.validator import validate_puzzle


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a fast diversity and validity stress test for the local generator.")
    parser.add_argument("--count", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=5610417)
    parser.add_argument("--validate-sample", type=int, default=500)
    parser.add_argument("--output", type=Path, default=Path("data/reports/improvement_2_stress_test.json"))
    args = parser.parse_args()

    started = time.perf_counter()
    generator = LocalTemplateGenerator()
    puzzles = generator.generate(count=args.count, seed=args.seed)
    elapsed = time.perf_counter() - started
    report = build_report(puzzles, args.count, args.seed, elapsed, args.validate_sample)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Generated {len(puzzles)} / {args.count} puzzles in {elapsed:.2f}s")
    print(f"Answer bank exact groups: {report['answer_bank']['exact_groups']}")
    print(f"Generated unique boards: {report['generated']['unique_boards']}")
    print(f"Generated duplicate boards: {report['generated']['duplicate_boards']}")
    print(f"Validation errors in sample: {report['validation_sample']['error_count']}")
    print(f"Wrote {args.output}")


def build_report(puzzles, requested: int, seed: int, elapsed: float, validate_sample: int) -> dict[str, Any]:
    bank_groups = {tuple(sorted(template.words)) for template in CATEGORY_BANK}
    bank_words = {word for template in CATEGORY_BANK for word in template.words}
    bank_categories = Counter(template.category for template in CATEGORY_BANK)
    board_counts: Counter[tuple[str, ...]] = Counter()
    group_counts: Counter[tuple[str, ...]] = Counter()
    word_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()
    strategy_counts: Counter[str] = Counter()

    for puzzle in puzzles:
        board_counts[tuple(sorted(puzzle.normalized_words()))] += 1
        word_counts.update(puzzle.normalized_words())
        strategy_counts[puzzle.source_strategy] += 1
        for group in puzzle.groups:
            group_counts[tuple(sorted(group.normalized_words()))] += 1
            category_counts[group.category] += 1

    validation_errors: list[dict[str, str]] = []
    for puzzle in puzzles[: max(0, validate_sample)]:
        for issue in validate_puzzle(puzzle):
            if issue.severity == "error":
                validation_errors.append({"puzzle_id": puzzle.id, "code": issue.code, "message": issue.message})

    return {
        "improvement": "Improvement 2",
        "purpose": "Stress-test the expanded offline generator without changing the curated web bank.",
        "parameters": {
            "requested": requested,
            "seed": seed,
            "validate_sample": validate_sample,
        },
        "runtime": {
            "seconds": round(elapsed, 3),
            "puzzles_per_second": round(len(puzzles) / elapsed, 2) if elapsed else 0.0,
        },
        "answer_bank": {
            "exact_groups": len(bank_groups),
            "unique_words": len(bank_words),
            "unique_categories": len(bank_categories),
            "top_categories": bank_categories.most_common(20),
        },
        "generated": {
            "count": len(puzzles),
            "unique_boards": len(board_counts),
            "duplicate_boards": sum(count - 1 for count in board_counts.values() if count > 1),
            "unique_exact_groups_used": len(group_counts),
            "duplicate_group_slots": sum(count - 1 for count in group_counts.values() if count > 1),
            "unique_words_used": len(word_counts),
            "max_word_count": max(word_counts.values(), default=0),
            "max_group_count": max(group_counts.values(), default=0),
            "max_category_count": max(category_counts.values(), default=0),
            "strategy_counts": dict(strategy_counts),
            "top_words": word_counts.most_common(20),
            "top_groups": [
                {"count": count, "words": list(signature)}
                for signature, count in group_counts.most_common(20)
            ],
            "top_categories": category_counts.most_common(20),
        },
        "validation_sample": {
            "checked": min(len(puzzles), max(0, validate_sample)),
            "error_count": len(validation_errors),
            "errors": validation_errors[:20],
        },
    }


if __name__ == "__main__":
    main()
