"""Extract the 26-feature plausibility vector for every puzzle in a set.

Reads a JSON list of puzzles, produces a CSV (and JSON) of feature
vectors plus the source tag. The result is the foundation for Phase 4:
distributional comparison, classifier training, and grouped summaries
in the technical appendix.

Usage:

  # NYT reference (calibration anchor)
  python scripts/extract_nyt_features.py \
      --input data/history/unified_reference.json \
      --source nyt \
      --out data/eval/features_nyt.json

  # Our curated 100
  python scripts/extract_nyt_features.py \
      --input data/puzzles/curated_100.json \
      --source generated_v1 \
      --out data/eval/features_curated_v1.json

  # Our upgraded curated 100 (after Phase 2)
  python scripts/extract_nyt_features.py \
      --input data/puzzles/curated_100_v2.json \
      --source generated_v2 \
      --out data/eval/features_curated_v2.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from infinite_connections.features import extract_features_batch, FEATURE_NAMES  # noqa: E402


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return path.name


def _load_puzzle_dicts(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, list) else payload.get("puzzles", [])


def _embed_words_factory():
    """Lazy-load MiniLM so scripts work even if the user hasn't run setup yet."""
    from infinite_connections.embedding_solver import default_solver
    solver = default_solver()
    return solver.embed_words


def _rhyme_tail_factory():
    """Wrap wordplay._phonemes + _rhyme_tail so features.py can call it."""
    from infinite_connections import wordplay as wp
    def fn(word: str) -> str | None:
        pron = wp._phonemes(word)
        if not pron:
            return None
        return wp._rhyme_tail(pron)
    return fn


def _zipf_factory():
    try:
        from wordfreq import zipf_frequency  # type: ignore[import-untyped]
        return lambda w: float(zipf_frequency(w.lower(), "en"))
    except ImportError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--source", required=True,
                        help="tag stored on each vector, e.g. 'nyt' or 'generated_v2'")
    parser.add_argument("--out", required=True)
    parser.add_argument("--skip-embeddings", action="store_true",
                        help="don't compute cohesion features (faster)")
    parser.add_argument("--skip-phonetic", action="store_true",
                        help="don't compute phonetic density feature")
    args = parser.parse_args()

    in_path = Path(args.input)
    if not in_path.is_absolute():
        in_path = ROOT / in_path
    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = ROOT / out_path

    puzzles = _load_puzzle_dicts(in_path)
    for p in puzzles:
        p["_source"] = args.source
    print(f"Loaded {len(puzzles)} puzzles from {_display_path(in_path)}")

    embeddings_fn = None if args.skip_embeddings else _embed_words_factory()
    rhyme_fn = None if args.skip_phonetic else _rhyme_tail_factory()
    zipf_fn = _zipf_factory()

    vectors = extract_features_batch(
        puzzles,
        embeddings_fn=embeddings_fn,
        rhyme_tail_fn=rhyme_fn,
        zipf_fn=zipf_fn,
    )

    payload = {
        "source": args.source,
        "feature_names": FEATURE_NAMES,
        "vectors": [
            {"puzzle_id": v.puzzle_id, "source": v.source, "values": v.values}
            for v in vectors
        ],
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {len(vectors)} feature vectors to {_display_path(out_path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
