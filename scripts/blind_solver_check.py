from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from infinite_connections.schema import Puzzle
from infinite_connections.solver import solve_puzzle, summarize_results


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an offline blind solver agreement check.")
    parser.add_argument("--input", type=Path, default=Path("data/puzzles/curated_100.json"))
    parser.add_argument("--output", type=Path, default=Path("data/reports/improvement_3_blind_solver_curated.json"))
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--max-solutions", type=int, default=25)
    args = parser.parse_args()

    raw = json.loads(args.input.read_text(encoding="utf-8"))
    puzzles = [Puzzle.from_dict(item) for item in raw[: args.limit]]
    results = [solve_puzzle(puzzle, max_solutions=args.max_solutions) for puzzle in puzzles]
    summary = summarize_results(results)
    payload: dict[str, Any] = {
        "improvement": "Improvement 3",
        "input": str(args.input).replace("\\", "/"),
        "max_solutions": args.max_solutions,
        "summary": summary,
        "results": [result.to_dict() for result in results],
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Checked {len(results)} puzzles from {args.input}")
    print(f"Unique-match rate: {summary['unique_match_rate']}")
    print(f"Status counts: {summary['status_counts']}")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
