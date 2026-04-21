from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from infinite_connections.schema import Puzzle


FIELDNAMES = [
    "review_rank",
    "puzzle_id",
    "sample_bucket",
    "title",
    "displayed_words",
    "category_1",
    "group_1_words",
    "category_2",
    "group_2_words",
    "category_3",
    "group_3_words",
    "category_4",
    "group_4_words",
    "auto_status",
    "auto_score",
    "review_status",
    "review_nyt_likeness",
    "review_clarity",
    "review_ambiguity_risk",
    "human_label",
    "human_ambiguity",
    "weakest_group",
    "would_show_instructor",
    "human_notes",
    "reviewer",
    "reviewed_at",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Export a CSV queue for manual puzzle review.")
    parser.add_argument("--puzzles", type=Path, default=Path("data/puzzles/candidates.json"))
    parser.add_argument("--quality", type=Path, default=Path("data/reports/quality_reports.json"))
    parser.add_argument("--judge", type=Path, default=Path("data/reports/judge_results.json"))
    parser.add_argument("--curated", type=Path, default=Path("data/puzzles/curated_100.json"))
    parser.add_argument("--output", type=Path, default=Path("reports/manual_review_queue.csv"))
    parser.add_argument("--dashboard", type=Path, default=Path("data/reports/dashboard.json"))
    parser.add_argument("--limit", type=int, default=500)
    args = parser.parse_args()

    puzzles = [Puzzle.from_dict(item) for item in read_json(args.puzzles, [])]
    quality_by_id = {item["puzzle_id"]: item for item in read_json(args.quality, []) if "puzzle_id" in item}
    judge_by_id = {
        item["puzzle_id"]: item
        for item in read_json(args.judge, {}).get("results", [])
        if isinstance(item, dict) and "puzzle_id" in item
    }
    curated_ids = {
        str(item.get("id"))
        for item in read_json(args.curated, [])
        if isinstance(item, dict) and item.get("id")
    }

    ordered = sorted(
        puzzles,
        key=lambda puzzle: review_sort_key(puzzle, curated_ids, quality_by_id, judge_by_id),
    )[: args.limit]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        for rank, puzzle in enumerate(ordered, start=1):
            writer.writerow(row_for_puzzle(rank, puzzle, curated_ids, quality_by_id, judge_by_id))
    update_dashboard(args.dashboard, args.output, len(ordered), curated_ids)
    print(f"Wrote {len(ordered)} review rows to {args.output}")


def read_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def review_sort_key(
    puzzle: Puzzle,
    curated_ids: set[str],
    quality_by_id: dict[str, dict[str, Any]],
    judge_by_id: dict[str, dict[str, Any]],
) -> tuple[int, float, str]:
    quality = quality_by_id.get(puzzle.id, {})
    judge = judge_by_id.get(puzzle.id)
    if puzzle.id in curated_ids:
        bucket = 0
    elif judge and judge.get("would_publish"):
        bucket = 1
    elif judge:
        bucket = 2
    elif quality.get("status") == "publish":
        bucket = 3
    else:
        bucket = 4
    score = float(quality.get("quality_score", 0.0) or 0.0)
    if judge:
        score += 0.25 * float(judge.get("nyt_likeness", 0.0) or 0.0)
        score += 0.25 * float(judge.get("clarity", 0.0) or 0.0)
        score -= 0.35 * float(judge.get("ambiguity_risk", 100.0) or 100.0)
    return (bucket, -score, puzzle.id)


def row_for_puzzle(
    rank: int,
    puzzle: Puzzle,
    curated_ids: set[str],
    quality_by_id: dict[str, dict[str, Any]],
    judge_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    quality = quality_by_id.get(puzzle.id, {})
    judge = judge_by_id.get(puzzle.id, {})
    groups = list(puzzle.groups)
    row: dict[str, Any] = {
        "review_rank": rank,
        "puzzle_id": puzzle.id,
        "sample_bucket": sample_bucket(puzzle.id, curated_ids, quality, judge),
        "title": puzzle.title,
        "displayed_words": "; ".join(puzzle.words),
        "auto_status": quality.get("status", ""),
        "auto_score": quality.get("quality_score", ""),
        "review_status": review_status(judge),
        "review_nyt_likeness": judge.get("nyt_likeness", ""),
        "review_clarity": judge.get("clarity", ""),
        "review_ambiguity_risk": judge.get("ambiguity_risk", ""),
        "human_label": "",
        "human_ambiguity": "",
        "weakest_group": "",
        "would_show_instructor": "",
        "human_notes": "",
        "reviewer": "",
        "reviewed_at": "",
    }
    for index in range(4):
        group = groups[index]
        row[f"category_{index + 1}"] = group.category
        row[f"group_{index + 1}_words"] = "; ".join(group.words)
    return row


def sample_bucket(
    puzzle_id: str,
    curated_ids: set[str],
    quality: dict[str, Any],
    judge: dict[str, Any],
) -> str:
    if puzzle_id in curated_ids:
        return "curated_100"
    if judge:
        return "review_pass" if judge.get("would_publish") else "review_flag"
    if quality.get("status") == "publish":
        return "high_auto_score"
    if quality.get("status") == "revise":
        return "borderline_auto"
    return "rejected_auto"


def review_status(judge: dict[str, Any]) -> str:
    if not judge:
        return "not_sampled"
    return "pass" if judge.get("would_publish") else "flag"


def update_dashboard(dashboard_path: Path, output_path: Path, row_count: int, curated_ids: set[str]) -> None:
    if dashboard_path.exists():
        dashboard = json.loads(dashboard_path.read_text(encoding="utf-8"))
    else:
        dashboard = {"summary": {}}
    dashboard["manual_review"] = {
        "queue_path": str(output_path).replace("\\", "/"),
        "target_reviews": row_count,
        "completed_reviews": 0,
        "curated_rows": len(curated_ids),
        "labels": {"good": 0, "borderline": 0, "bad": 0},
        "note": "A 500-row review queue is exported for human spot checks before final submission.",
    }
    notes = [
        "The large generator path is local and reproducible, so instructor-side stress tests do not require paid API calls.",
        "The curated play bank contains 100 puzzles selected from automatic checks and sampled editor review.",
        "Historical reference data is loaded for mechanism analysis and near-duplicate checks.",
        "Manual spot-check results should be entered in reports/manual_review_queue.csv before final write-up.",
    ]
    dashboard["evidence_notes"] = notes
    dashboard_path.parent.mkdir(parents=True, exist_ok=True)
    dashboard_path.write_text(json.dumps(dashboard, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
