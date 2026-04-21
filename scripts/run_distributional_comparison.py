"""Compare generated-puzzle feature distributions to NYT reference distributions.

Given two feature JSONs produced by extract_nyt_features.py, compute
per-feature Wasserstein-1 distance (fallback to mean absolute difference
if scipy is unavailable), aggregate into an overall distance, and write
a human-readable report for the technical appendix.

Usage:

    python scripts/run_distributional_comparison.py \
        --nyt data/eval/features_nyt.json \
        --ours data/eval/features_curated_v2.json \
        --out data/eval/distribution_comparison_v2.json

The JSON output has:
    {
      "overall_distance": float,
      "per_feature": {feature_name: distance, ...},
      "interpretation": {feature_name: "closer|farther|neutral"},
      "summary": "..."
    }
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from infinite_connections.features import FEATURE_NAMES, distribution_distance, FeatureVector  # noqa: E402


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return path.name


def _load_vectors(path: Path) -> list[FeatureVector]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [
        FeatureVector(
            puzzle_id=v["puzzle_id"],
            values=list(v["values"]),
            source=v.get("source", "unknown"),
        )
        for v in payload.get("vectors", [])
    ]


def _interpret(distance: float) -> str:
    if distance < 0.05:
        return "close"
    if distance < 0.15:
        return "moderate"
    return "far"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--nyt", required=True)
    parser.add_argument("--ours", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    nyt_path = Path(args.nyt) if Path(args.nyt).is_absolute() else ROOT / args.nyt
    ours_path = Path(args.ours) if Path(args.ours).is_absolute() else ROOT / args.ours
    out_path = Path(args.out) if Path(args.out).is_absolute() else ROOT / args.out

    nyt_vectors = _load_vectors(nyt_path)
    our_vectors = _load_vectors(ours_path)
    if not nyt_vectors or not our_vectors:
        print("Empty feature set on one side; aborting.", file=sys.stderr)
        return 2

    report = distribution_distance(nyt_vectors, our_vectors)
    report["interpretation"] = {
        name: _interpret(dist) for name, dist in report["per_feature"].items()
    }
    close = sum(1 for v in report["interpretation"].values() if v == "close")
    total = len(report["interpretation"])
    report["summary"] = (
        f"{close}/{total} features match NYT closely "
        f"(overall Wasserstein-mean = {report['overall']:.4f} across {total} features). "
        f"Lower is closer to NYT."
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(report["summary"])
    print(f"Wrote {_display_path(out_path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
