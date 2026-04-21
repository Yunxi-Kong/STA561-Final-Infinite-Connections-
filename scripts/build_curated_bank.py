from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from infinite_connections.schema import Puzzle
from infinite_connections.solver import solve_puzzle


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a fixed curated puzzle bank for the web demo.")
    parser.add_argument("--puzzles", type=Path, default=Path("data/puzzles/published.json"))
    parser.add_argument("--quality", type=Path, default=Path("data/reports/quality_reports.json"))
    parser.add_argument("--judge", type=Path, default=Path("data/reports/judge_results.json"))
    parser.add_argument("--dashboard", type=Path, default=Path("data/reports/dashboard.json"))
    parser.add_argument("--output", type=Path, default=Path("data/puzzles/curated_100.json"))
    parser.add_argument("--audit-output", type=Path, default=Path("data/reports/diversity_report.json"))
    parser.add_argument("--strong-output", type=Path, default=Path("data/puzzles/strong_demo.json"))
    parser.add_argument("--target", type=int, default=100)
    parser.add_argument("--max-word-uses", type=int, default=5)
    parser.add_argument("--max-group-uses", type=int, default=1)
    parser.add_argument("--max-category-uses", type=int, default=4)
    parser.add_argument("--require-solver-unique", action="store_true", help="Keep only puzzles with a unique blind-solver match.")
    args = parser.parse_args()

    puzzles = [Puzzle.from_dict(item) for item in read_json(args.puzzles, [])]
    quality_by_id = {item["puzzle_id"]: item for item in read_json(args.quality, []) if "puzzle_id" in item}
    judge_payload = read_json(args.judge, {})
    judge_by_id = {
        item["puzzle_id"]: item
        for item in judge_payload.get("results", [])
        if isinstance(item, dict) and "puzzle_id" in item
    }

    ranked = rank_puzzles(puzzles, quality_by_id, judge_by_id)
    selected, dropped = select_diverse(
        ranked,
        target=args.target,
        max_word_uses=args.max_word_uses,
        max_group_uses=args.max_group_uses,
        max_category_uses=args.max_category_uses,
        require_solver_unique=args.require_solver_unique,
    )
    selected = order_for_presentation(selected)
    output = [
        enrich_puzzle(puzzle, index, quality_by_id.get(puzzle.id), judge_by_id.get(puzzle.id))
        for index, puzzle in enumerate(selected, start=1)
    ]
    audit = build_diversity_audit(puzzles, selected, dropped, args)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.audit_output.parent.mkdir(parents=True, exist_ok=True)
    args.audit_output.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.strong_output.parent.mkdir(parents=True, exist_ok=True)
    args.strong_output.write_text(json.dumps(output[: min(50, len(output))], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    update_dashboard(args.dashboard, selected, quality_by_id, judge_by_id, args.output, audit, judge_payload)
    print(f"Wrote {len(output)} curated puzzles to {args.output}")
    print(f"Wrote diversity audit to {args.audit_output}")


def read_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def rank_puzzles(
    puzzles: list[Puzzle],
    quality_by_id: dict[str, dict[str, Any]],
    judge_by_id: dict[str, dict[str, Any]],
) -> list[tuple[float, Puzzle]]:
    ranked: list[tuple[float, Puzzle]] = []
    for puzzle in puzzles:
        quality = quality_by_id.get(puzzle.id, {})
        judge = judge_by_id.get(puzzle.id)
        score = float(quality.get("quality_score", 0.0) or 0.0)
        if judge:
            score += 200.0 if judge.get("would_publish") else -200.0
            score += 0.35 * float(judge.get("nyt_likeness", 0.0) or 0.0)
            score += 0.30 * float(judge.get("clarity", 0.0) or 0.0)
            score -= 0.45 * float(judge.get("ambiguity_risk", 100.0) or 100.0)
        score += strategy_bonus(puzzle.source_strategy)
        ranked.append((score, puzzle))
    ranked.sort(key=lambda item: (item[0], item[1].id), reverse=True)
    return ranked


def strategy_bonus(strategy: str) -> float:
    strategy = strategy.lower()
    bonus = 0.0
    if "wordplay" in strategy:
        bonus += 6.0
    if "phrase_completion" in strategy:
        bonus += 4.0
    if strategy.count("+") >= 1:
        bonus += 2.0
    return bonus


def select_diverse(
    ranked: list[tuple[float, Puzzle]],
    target: int,
    max_word_uses: int,
    max_group_uses: int,
    max_category_uses: int,
    require_solver_unique: bool,
) -> tuple[list[Puzzle], Counter[str]]:
    selected: list[Puzzle] = []
    seen_signatures: set[tuple[str, ...]] = set()
    strategy_counts: Counter[str] = Counter()
    word_counts: Counter[str] = Counter()
    group_counts: Counter[tuple[str, ...]] = Counter()
    category_counts: Counter[str] = Counter()
    dropped: Counter[str] = Counter()

    for _, puzzle in ranked:
        if len(selected) >= target:
            break
        signature = tuple(sorted(puzzle.normalized_words()))
        if signature in seen_signatures:
            dropped["duplicate_board"] += 1
            continue
        group_signatures = [group_signature(group.words) for group in puzzle.groups]
        if any(group_counts[signature] >= max_group_uses for signature in group_signatures):
            dropped["duplicate_answer_group"] += 1
            continue
        words = [word for group in puzzle.groups for word in group.normalized_words()]
        if any(word_counts[word] >= max_word_uses for word in words):
            dropped["word_frequency_cap"] += 1
            continue
        categories = [group.category for group in puzzle.groups]
        if any(category_counts[category] >= max_category_uses for category in categories):
            dropped["category_frequency_cap"] += 1
            continue
        strategy = puzzle.source_strategy
        if strategy_counts[strategy] >= max(8, target // 2) and len(selected) < target * 0.8:
            dropped["strategy_balance_cap"] += 1
            continue
        if require_solver_unique and solve_puzzle(puzzle).status != "unique_match":
            dropped["blind_solver_not_unique"] += 1
            continue

        selected.append(puzzle)
        seen_signatures.add(signature)
        strategy_counts[strategy] += 1
        word_counts.update(words)
        group_counts.update(group_signatures)
        category_counts.update(categories)

    if len(selected) < target:
        raise RuntimeError(
            f"Only selected {len(selected)} puzzles under diversity constraints; "
            f"generate more candidates or expand the seed bank."
        )

    return selected, dropped


def order_for_presentation(puzzles: list[Puzzle]) -> list[Puzzle]:
    indexed = list(enumerate(puzzles))
    indexed.sort(key=lambda item: presentation_key(item[1], item[0]))
    return [puzzle for _, puzzle in indexed]


def presentation_key(puzzle: Puzzle, original_index: int) -> tuple[int, int, int]:
    category_text = " ".join(group.category.lower() for group in puzzle.groups)
    has_memorable_repeated_words = int(
        any(token in category_text for token in ("palindrome", "homophone", "nato alphabet"))
    )
    has_wordplay = int("wordplay" in puzzle.source_strategy)
    has_phrase = int("phrase_completion" in puzzle.source_strategy)
    return (has_memorable_repeated_words, has_wordplay, -has_phrase, original_index)


def enrich_puzzle(
    puzzle: Puzzle,
    rank: int,
    quality: dict[str, Any] | None,
    judge: dict[str, Any] | None,
) -> dict[str, Any]:
    data = puzzle.to_dict()
    final_title = f"Puzzle {rank:03d}"
    category_names = ", ".join(group.category for group in puzzle.groups)
    data["title"] = final_title
    data["source"] = "Curated puzzle bank"
    data["strategy"] = puzzle.source_strategy
    data["difficulty"] = "Balanced"
    data["curator_note"] = (
        f"{final_title} contains four compact groups: {category_names}. "
        "The board is designed to be played first, with the answer structure available in Review mode."
    )
    data["curation_rank"] = rank
    data["quality_score"] = quality.get("quality_score") if quality else None
    data["review_status"] = review_status(judge)
    data["review_summary"] = {
        "sampled": bool(judge),
        "would_publish": bool(judge.get("would_publish")) if judge else None,
        "nyt_likeness": judge.get("nyt_likeness") if judge else None,
        "clarity": judge.get("clarity") if judge else None,
        "ambiguity_risk": judge.get("ambiguity_risk") if judge else None,
    }
    return data


def group_signature(words: list[str]) -> tuple[str, ...]:
    return tuple(sorted(str(word).strip().upper() for word in words))


def review_status(judge: dict[str, Any] | None) -> str:
    if not judge:
        return "automatic_screened"
    return "sample_review_pass" if judge.get("would_publish") else "sample_review_flag"


def build_diversity_audit(
    all_puzzles: list[Puzzle],
    selected: list[Puzzle],
    dropped: Counter[str],
    args: argparse.Namespace,
) -> dict[str, Any]:
    before = diversity_snapshot(all_puzzles)
    after = diversity_snapshot(selected)
    after["unique_titles"] = len(selected)
    after["duplicate_title_slots"] = 0
    after["top_titles"] = [(f"Puzzle {index:03d}", 1) for index in range(1, min(20, len(selected)) + 1)]
    return {
        "policy": {
            "target": args.target,
            "max_word_uses": args.max_word_uses,
            "max_exact_group_uses": args.max_group_uses,
            "max_category_uses": args.max_category_uses,
            "title_policy": "neutral_numbered_titles",
            "require_solver_unique": args.require_solver_unique,
        },
        "before": before,
        "after": after,
        "dropped_reasons": dict(dropped.most_common()),
        "passed": {
            "target_count": len(selected) == args.target,
            "duplicate_exact_groups": after["duplicate_exact_group_slots"] == 0,
            "duplicate_titles": after["duplicate_title_slots"] == 0,
            "max_word_count": after["max_word_count"] <= args.max_word_uses,
        },
    }


def diversity_snapshot(puzzles: list[Puzzle]) -> dict[str, Any]:
    word_counts: Counter[str] = Counter()
    group_counts: Counter[tuple[str, ...]] = Counter()
    category_counts: Counter[str] = Counter()
    title_counts: Counter[str] = Counter(puzzle.title for puzzle in puzzles)
    for puzzle in puzzles:
        word_counts.update(puzzle.normalized_words())
        for group in puzzle.groups:
            group_counts[group_signature(group.words)] += 1
            category_counts[group.category] += 1
    duplicate_groups = [count - 1 for count in group_counts.values() if count > 1]
    duplicate_titles = [count - 1 for count in title_counts.values() if count > 1]
    return {
        "puzzle_count": len(puzzles),
        "unique_words": len(word_counts),
        "word_slots": sum(word_counts.values()),
        "max_word_count": max(word_counts.values(), default=0),
        "top_words": word_counts.most_common(20),
        "unique_exact_groups": len(group_counts),
        "duplicate_exact_group_slots": sum(duplicate_groups),
        "top_exact_groups": [
            {"count": count, "words": list(signature)}
            for signature, count in group_counts.most_common(20)
            if count > 1
        ],
        "unique_categories": len(category_counts),
        "top_categories": category_counts.most_common(20),
        "unique_titles": len(title_counts),
        "duplicate_title_slots": sum(duplicate_titles),
        "top_titles": title_counts.most_common(20),
    }


def update_dashboard(
    dashboard_path: Path,
    selected: list[Puzzle],
    quality_by_id: dict[str, dict[str, Any]],
    judge_by_id: dict[str, dict[str, Any]],
    output_path: Path,
    audit: dict[str, Any],
    judge_payload: dict[str, Any],
) -> None:
    if dashboard_path.exists():
        dashboard = json.loads(dashboard_path.read_text(encoding="utf-8"))
    else:
        dashboard = {"summary": {}}
    sampled = [judge_by_id[puzzle.id] for puzzle in selected if puzzle.id in judge_by_id]
    sample_pass = sum(1 for item in sampled if item.get("would_publish"))
    scores = [
        float(quality_by_id.get(puzzle.id, {}).get("quality_score", 0.0) or 0.0)
        for puzzle in selected
    ]
    dashboard["curated_bank"] = {
        "path": str(output_path).replace("\\", "/"),
        "count": len(selected),
        "sample_reviewed": len(sampled),
        "sample_review_pass": sample_pass,
        "sample_review_pass_rate": round(sample_pass / len(sampled), 3) if sampled else None,
        "average_quality_score": round(sum(scores) / len(scores), 2) if scores else 0.0,
        "strategy_counts": dict(Counter(puzzle.source_strategy for puzzle in selected)),
        "diversity": {
            "max_word_count": audit["after"]["max_word_count"],
            "duplicate_exact_group_slots": audit["after"]["duplicate_exact_group_slots"],
            "duplicate_title_slots": audit["after"]["duplicate_title_slots"],
            "unique_words": audit["after"]["unique_words"],
        },
    }
    dashboard.setdefault("summary", {})["curated"] = len(selected)
    if judge_payload.get("summary"):
        provider_used = judge_payload.get("provider_used", "unknown")
        dashboard["summary"]["evidence_level"] = (
            "automatic_screen_plus_sample_screen"
            if provider_used in {"openai", "mixed_openai_offline_fallback"}
            else "automatic_screen_plus_offline_screen"
        )
        dashboard["sample_screen"] = {
            "summary": sanitize_sample_summary(judge_payload.get("summary", {})),
            "note": "This cached sample screen is a calibration signal; the large generator path remains local and reproducible.",
        }
        dashboard.pop("editor_review", None)
        dashboard.pop("llm_review", None)
    dashboard["diversity_audit"] = audit
    dashboard_path.parent.mkdir(parents=True, exist_ok=True)
    dashboard_path.write_text(json.dumps(dashboard, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sanitize_sample_summary(summary: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "count",
        "would_publish",
        "would_publish_rate",
        "average_nyt_likeness",
        "average_clarity",
        "average_ambiguity_risk",
        "label_counts",
    }
    return {key: value for key, value in summary.items() if key in allowed}


if __name__ == "__main__":
    main()
