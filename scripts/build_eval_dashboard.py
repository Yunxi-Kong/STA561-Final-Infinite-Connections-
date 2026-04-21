"""Build a compact dashboard JSON from the current v2 experiment outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _read(path: Path, fallback):
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-audit", default="data/eval/audit_candidates_v2_10k_mixed_offline_final.json")
    parser.add_argument("--curated-audit", default="data/eval/audit_curated_100_v2.json")
    parser.add_argument("--distribution", default="data/eval/distribution_comparison_v2.json")
    parser.add_argument("--classifier", default="data/eval/plausibility_curated_v2.json")
    parser.add_argument("--out", default="data/reports/dashboard.json")
    args = parser.parse_args()

    batch = _read(ROOT / args.batch_audit, {})
    curated = _read(ROOT / args.curated_audit, {})
    distribution = _read(ROOT / args.distribution, {})
    classifier = _read(ROOT / args.classifier, {})
    score_report = classifier.get("score_report", {})

    dashboard = {
        "summary": {
            "generated": batch.get("count", 0),
            "accepted": batch.get("count", 0) - batch.get("malformed", 0),
            "published": curated.get("count", 0),
            "curated": curated.get("count", 0),
            "quality_gate": "continue",
            "evidence_level": "automatic_screen_plus_distributional_eval",
            "history_exact_overlap": batch.get("history_overlap", {}).get("exact_overlap_count", 0),
            "blind_unique_match_rate": curated.get("blind_solver_sample", {}).get("unique_match_rate"),
            "nyt_feature_distance": distribution.get("overall"),
            "classifier_pass_rate": score_report.get("pass_rate_at_0.5"),
        },
        "curated_bank": {
            "path": "data/puzzles/curated_100_v2.json",
            "count": curated.get("count", 0),
            "diversity": {
                "unique_boards": curated.get("unique_boards", 0),
                "unique_exact_groups": curated.get("unique_exact_groups", 0),
                "duplicate_exact_group_slots": curated.get("duplicate_exact_group_slots", 0),
                "duplicate_board_slots": curated.get("duplicate_board_slots", 0),
                "unique_words": curated.get("unique_words", 0),
                "max_word_count": curated.get("max_word_count", 0),
                "max_group_count": curated.get("max_group_count", 0),
                "max_category_count": curated.get("max_category_count", 0),
            },
            "blind_solver": curated.get("blind_solver_sample", {}),
            "history_overlap": curated.get("history_overlap", {}),
            "strategy_counts": curated.get("strategy_counts", {}),
        },
        "batch_audit": {
            "path": "data/puzzles/candidates_v2_10k_mixed_offline_final.json",
            "count": batch.get("count", 0),
            "unique_boards": batch.get("unique_boards", 0),
            "duplicate_board_slots": batch.get("duplicate_board_slots", 0),
            "history_overlap": batch.get("history_overlap", {}),
            "blind_solver_sample": batch.get("blind_solver_sample", {}),
            "validation_sample": batch.get("validation_sample", {}),
            "strategy_counts": batch.get("strategy_counts", {}),
        },
        "distributional_eval": {
            "overall": distribution.get("overall"),
            "summary": distribution.get("summary", ""),
            "interpretation": distribution.get("interpretation", {}),
        },
        "classifier_eval": {
            "model": classifier.get("model"),
            "test_f1": classifier.get("test_f1"),
            "test_auc": classifier.get("test_auc"),
            "score_report": score_report,
        },
        "strategyRates": [
            {"name": name, "value": count / max(1, batch.get("count", 0))}
            for name, count in batch.get("strategy_counts", {}).items()
        ],
        "rejectionReasons": [
            {"name": "historical_exact_overlap", "value": batch.get("history_overlap", {}).get("exact_overlap_count", 0)},
            {"name": "validation_errors_sample", "value": batch.get("validation_sample", {}).get("error_count", 0)},
            {"name": "curated_duplicate_groups", "value": curated.get("duplicate_exact_group_slots", 0)},
        ],
        "scoreBands": [
            {"name": "classifier_pass", "value": score_report.get("pass_rate_at_0.5", 0)},
            {"name": "blind_unique_curated", "value": curated.get("blind_solver_sample", {}).get("unique_match_rate", 0)},
            {"name": "blind_unique_10k_sample", "value": batch.get("blind_solver_sample", {}).get("unique_match_rate", 0)},
        ],
        "notes": [
            "The playable bank uses the v2 curated set.",
            "Large-batch generation is local and reproducible.",
            "External LLM solvers remain optional because free-tier availability varies.",
        ],
    }

    out_path = ROOT / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(dashboard, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
