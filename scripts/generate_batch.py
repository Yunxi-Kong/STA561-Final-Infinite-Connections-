from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from infinite_connections.batch import run_batch, write_batch_outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate and score Infinite Connections candidate puzzles.")
    parser.add_argument("--count", type=int, default=100, help="Number of candidate puzzles to generate.")
    parser.add_argument("--seed", type=int, default=561, help="Random seed for local generation.")
    parser.add_argument("--provider", choices=["local", "openai"], default="local", help="Generation provider.")
    parser.add_argument("--data-dir", type=Path, default=Path("data"), help="Output data directory.")
    parser.add_argument(
        "--reference",
        type=Path,
        default=Path("data/history/reference_sets.json"),
        help="Reference word-set data for duplicate checks.",
    )
    args = parser.parse_args()

    result = run_batch(
        count=args.count,
        seed=args.seed,
        provider=args.provider,
        reference_path=args.reference,
    )
    paths = write_batch_outputs(result, args.data_dir)
    print(f"Generated {len(result.candidates)} candidates")
    print(f"Published {len(result.published)} | Revise {len(result.revised)} | Rejected {len(result.rejected)}")
    for label, path in paths.items():
        print(f"{label}: {path}")


if __name__ == "__main__":
    main()
