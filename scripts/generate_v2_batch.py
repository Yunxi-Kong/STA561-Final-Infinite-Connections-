"""Generate puzzles with the v2 generator (theme-first + wordplay).

Usage on your Windows box (after RUN_SETUP.bat succeeded and Ollama is up):

  # Small sanity batch
  python scripts/generate_v2_batch.py --count 50 --seed 561 \
      --out data/puzzles/candidates_v2_small.json

  # Production-scale batch (10K, reproducible)
  python scripts/generate_v2_batch.py --count 10000 --seed 561 \
      --out data/puzzles/candidates_v2_10k.json

  # Template-only (skip Ollama entirely, for offline reproducibility)
  python scripts/generate_v2_batch.py --count 10000 --seed 561 --mode template \
      --out data/puzzles/candidates_v2_10k_offline.json

The output file is a JSON list of Puzzle dicts compatible with the rest
of the pipeline (blind_solver_check.py, run_multi_solver_eval.py, etc.).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from time import time

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from infinite_connections.generator_v2 import GeneratorV2  # noqa: E402
from infinite_connections.validator import score_puzzle  # noqa: E402


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return path.name


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--seed", type=int, default=561)
    parser.add_argument("--mode", choices=["template", "theme_first", "mixed"],
                        default="mixed")
    parser.add_argument("--theme-prob", type=float, default=0.6,
                        help="only used when --mode=mixed")
    parser.add_argument("--out", required=True)
    parser.add_argument("--skip-ollama", action="store_true",
                        help="force template mode even if Ollama is up")
    parser.add_argument("--offline-themes", action="store_true",
                        help="allow theme_first/mixed, but use cached offline themes instead of Ollama")
    parser.add_argument("--no-rewrite", action="store_true",
                        help="do not use Ollama to rewrite category names")
    parser.add_argument("--validate", action="store_true",
                        help="run score_puzzle on every puzzle")
    args = parser.parse_args()

    if args.skip_ollama:
        mode = "template"
    else:
        mode = args.mode

    gen = GeneratorV2(
        mode=mode,
        theme_first_probability=args.theme_prob,
        rewrite_categories_with_ollama=not args.no_rewrite,
        use_ollama=not args.offline_themes,
    )

    start = time()
    puzzles = gen.generate(count=args.count, seed=args.seed)
    elapsed = time() - start

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = ROOT / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)

    serialised = []
    rejections = 0
    for p in puzzles:
        if args.validate:
            report = score_puzzle(p)
            if report.status == "reject":
                rejections += 1
                continue
        serialised.append(p.to_dict())

    out_path.write_text(json.dumps(serialised, indent=2), encoding="utf-8")

    print(f"Generated {len(puzzles)} puzzles in {elapsed:.1f}s")
    print(f"Validation rejections: {rejections}")
    print(f"Wrote {len(serialised)} puzzles to {_display_path(out_path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
