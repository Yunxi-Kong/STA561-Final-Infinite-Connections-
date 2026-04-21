"""Train a NYT-likeness classifier on the 26-feature vectors.

Positive class: NYT historical puzzles (from features_nyt.json).
Negative class: random 4-partitions of random 16-word samples
               (synthesised in-script from the NYT corpus's vocabulary).

We deliberately use the SAME feature extractor as the positive puzzles
so the classifier learns structural properties, not content.

Outputs:
  - data/eval/plausibility_classifier.json
      metrics (precision/recall/F1/AUC), feature importances, model params
  - data/eval/plausibility_classifier.joblib
      pickled sklearn / xgboost model for reuse

Usage:

    python scripts/train_plausibility_classifier.py \
        --nyt-features data/eval/features_nyt.json \
        --out-report data/eval/plausibility_classifier.json \
        --out-model data/eval/plausibility_classifier.joblib

Then score your generated puzzles:

    python scripts/train_plausibility_classifier.py \
        --nyt-features data/eval/features_nyt.json \
        --score data/eval/features_curated_v2.json \
        --out-report data/eval/plausibility_curated_v2.json
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from infinite_connections.features import FEATURE_NAMES  # noqa: E402


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return path.name


def _load_features(path: Path) -> tuple[np.ndarray, list[str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    vectors = payload.get("vectors", [])
    if not vectors:
        return np.empty((0, len(FEATURE_NAMES))), []
    matrix = np.array([v["values"] for v in vectors], dtype=np.float64)
    ids = [v["puzzle_id"] for v in vectors]
    return matrix, ids


def _synthesise_negative(corpus_path: Path, count: int, rng: random.Random) -> np.ndarray:
    """Build synthetic bad puzzles by randomly partitioning real NYT words.

    For each synthetic puzzle:
      1. Draw 16 random words from the NYT vocabulary.
      2. Assign them to 4 random groups of 4.
      3. Build a minimal puzzle dict and extract its feature vector.

    We expect these to score *lower* than real NYT puzzles on intra-group
    cohesion, and provide a natural negative class.
    """
    from infinite_connections.features import extract_features

    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    if isinstance(corpus, dict):
        corpus = corpus.get("puzzles", [])
    vocabulary: list[str] = []
    for puzzle in corpus:
        vocabulary.extend(str(w).upper() for w in puzzle.get("words", []))
    vocabulary = sorted(set(vocabulary))
    if len(vocabulary) < 64:
        raise RuntimeError("Not enough vocabulary to synthesise negatives")

    negatives: list[np.ndarray] = []
    for i in range(count):
        words = rng.sample(vocabulary, 16)
        groups = []
        for gi in range(4):
            group_words = words[gi * 4 : (gi + 1) * 4]
            groups.append({
                "category": f"Random group {gi}",
                "words": group_words,
                "difficulty": rng.choice(["yellow", "green", "blue", "purple"]),
                "strategy": "random",
            })
        puzzle_dict = {
            "id": f"neg-{i}",
            "words": words,
            "groups": groups,
            "_source": "negative",
        }
        vec = extract_features(puzzle_dict)
        negatives.append(vec.as_array())
    return np.vstack(negatives)


def _train(X: np.ndarray, y: np.ndarray) -> dict:
    """Fit a gradient-boosted classifier with held-out F1 + AUC."""
    try:
        from sklearn.model_selection import train_test_split  # type: ignore[import-untyped]
        from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score  # type: ignore[import-untyped]
    except ImportError:
        raise RuntimeError("scikit-learn missing; run setup_env.py first.")

    try:
        from xgboost import XGBClassifier  # type: ignore[import-untyped]
        clf = XGBClassifier(
            n_estimators=200, max_depth=4, learning_rate=0.1,
            eval_metric="logloss", use_label_encoder=False,
            random_state=561,
        )
        model_name = "XGBClassifier"
    except ImportError:
        from sklearn.linear_model import LogisticRegression  # type: ignore[import-untyped]
        clf = LogisticRegression(max_iter=1000, random_state=561)
        model_name = "LogisticRegression"

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=561, stratify=y
    )
    clf.fit(X_train, y_train)
    preds = clf.predict(X_test)
    probs = clf.predict_proba(X_test)[:, 1]

    importances = {}
    if hasattr(clf, "feature_importances_"):
        importances = dict(zip(FEATURE_NAMES, clf.feature_importances_.tolist()))
    elif hasattr(clf, "coef_"):
        importances = dict(zip(FEATURE_NAMES, clf.coef_[0].tolist()))

    return {
        "model": model_name,
        "train_size": int(len(X_train)),
        "test_size": int(len(X_test)),
        "test_precision": float(precision_score(y_test, preds, zero_division=0)),
        "test_recall": float(recall_score(y_test, preds, zero_division=0)),
        "test_f1": float(f1_score(y_test, preds, zero_division=0)),
        "test_auc": float(roc_auc_score(y_test, probs)),
        "feature_importances": importances,
        "classifier": clf,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--nyt-features", required=True,
                        help="positive-class features (from extract_nyt_features.py)")
    parser.add_argument("--corpus", default="data/history/unified_reference.json",
                        help="used to synthesise random-partition negatives")
    parser.add_argument("--negative-ratio", type=float, default=1.0)
    parser.add_argument("--score",
                        help="if set, path to a features JSON to score "
                             "(skips training + fits from the nyt features)")
    parser.add_argument("--out-report", required=True)
    parser.add_argument("--out-model", default="")
    parser.add_argument("--seed", type=int, default=561)
    args = parser.parse_args()

    nyt_path = Path(args.nyt_features) if Path(args.nyt_features).is_absolute() else ROOT / args.nyt_features
    corpus_path = Path(args.corpus) if Path(args.corpus).is_absolute() else ROOT / args.corpus
    out_report = Path(args.out_report) if Path(args.out_report).is_absolute() else ROOT / args.out_report
    out_model = Path(args.out_model) if args.out_model else None

    rng = random.Random(args.seed)
    X_pos, _ids_pos = _load_features(nyt_path)
    if X_pos.shape[0] == 0:
        print("No positive features found; aborting.", file=sys.stderr)
        return 2

    n_neg = max(200, int(X_pos.shape[0] * args.negative_ratio))
    X_neg = _synthesise_negative(corpus_path, count=n_neg, rng=rng)

    X = np.vstack([X_pos, X_neg])
    y = np.concatenate([np.ones(X_pos.shape[0]), np.zeros(X_neg.shape[0])])

    results = _train(X, y)
    clf = results.pop("classifier")

    # Optional scoring pass.
    score_report = None
    if args.score:
        score_path = Path(args.score) if Path(args.score).is_absolute() else ROOT / args.score
        X_score, score_ids = _load_features(score_path)
        probs = clf.predict_proba(X_score)[:, 1].tolist()
        passing = sum(1 for p in probs if p >= 0.5)
        score_report = {
            "n": int(X_score.shape[0]),
            "pass_at_0.5": int(passing),
            "pass_rate_at_0.5": float(passing / max(1, X_score.shape[0])),
            "mean_probability": float(np.mean(probs)) if probs else 0.0,
            "per_puzzle": dict(zip(score_ids, probs)),
        }
        results["score_report"] = score_report

    out_report.parent.mkdir(parents=True, exist_ok=True)
    out_report.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("Classifier trained:")
    print(f"  model       : {results['model']}")
    print(f"  test F1     : {results['test_f1']:.3f}")
    print(f"  test AUC    : {results['test_auc']:.3f}")
    if score_report:
        print(f"  pass rate   : {score_report['pass_rate_at_0.5']:.3f} "
              f"({score_report['pass_at_0.5']}/{score_report['n']})")

    if out_model:
        try:
            import joblib  # type: ignore[import-untyped]
            joblib.dump(clf, out_model)
            print(f"  model saved : {_display_path(out_model)}")
        except ImportError:
            print("  (joblib not installed; skipping model save)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
