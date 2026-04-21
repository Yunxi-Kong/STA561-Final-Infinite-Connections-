"""Batch generation, evaluation, and cache writing."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .generator import LocalTemplateGenerator, OpenAIStructuredGenerator, PuzzleGenerator
from .history import load_reference_sets, nearest_reference
from .schema import Puzzle, QualityReport
from .validator import score_puzzle


@dataclass(slots=True)
class BatchResult:
    candidates: list[Puzzle]
    reports: list[QualityReport]

    def by_status(self, status: str) -> list[Puzzle]:
        status_by_id = {report.puzzle_id: report.status for report in self.reports}
        return [puzzle for puzzle in self.candidates if status_by_id.get(puzzle.id) == status]

    @property
    def published(self) -> list[Puzzle]:
        return self.by_status("publish")

    @property
    def revised(self) -> list[Puzzle]:
        return self.by_status("revise")

    @property
    def rejected(self) -> list[Puzzle]:
        return self.by_status("reject")


def generator_for(provider: str) -> PuzzleGenerator:
    if provider == "local":
        return LocalTemplateGenerator()
    if provider == "openai":
        return OpenAIStructuredGenerator()
    raise ValueError(f"Unknown provider: {provider}")


def run_batch(count: int, seed: int | None, provider: str, reference_path: Path) -> BatchResult:
    generator = generator_for(provider)
    references = load_reference_sets(reference_path)
    candidates = generator.generate(count=count, seed=seed)
    reports = [score_puzzle(puzzle, nearest_reference=nearest_reference(puzzle, references)) for puzzle in candidates]
    return BatchResult(candidates=candidates, reports=reports)


def write_batch_outputs(result: BatchResult, output_root: Path) -> dict[str, Path]:
    puzzle_dir = output_root / "puzzles"
    report_dir = output_root / "reports"
    puzzle_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    paths = {
        "candidates": puzzle_dir / "candidates.json",
        "published": puzzle_dir / "published.json",
        "revised": puzzle_dir / "revised.json",
        "rejected": puzzle_dir / "rejected.json",
        "quality_reports": report_dir / "quality_reports.json",
        "dashboard": report_dir / "dashboard.json",
    }
    write_json(paths["candidates"], [puzzle.to_dict() for puzzle in result.candidates])
    ranked = rank_puzzles(result)
    write_json(paths["published"], [puzzle.to_dict() for puzzle in ranked["publish"]])
    write_json(paths["revised"], [puzzle.to_dict() for puzzle in result.revised])
    write_json(paths["rejected"], [puzzle.to_dict() for puzzle in result.rejected])
    write_json(paths["quality_reports"], [report.to_dict() for report in result.reports])
    write_json(paths["dashboard"], build_dashboard(result))
    return paths


def rank_puzzles(result: BatchResult) -> dict[str, list[Puzzle]]:
    report_by_id = {report.puzzle_id: report for report in result.reports}
    ranked: dict[str, list[Puzzle]] = {}
    for status in ("publish", "revise", "reject"):
        ranked[status] = sorted(
            result.by_status(status),
            key=lambda puzzle: report_by_id[puzzle.id].quality_score,
            reverse=True,
        )
    return ranked


def build_dashboard(result: BatchResult) -> dict[str, Any]:
    status_counts = Counter(report.status for report in result.reports)
    rejection_counts: Counter[str] = Counter()
    score_by_status: dict[str, list[float]] = defaultdict(list)
    report_by_id = {report.puzzle_id: report for report in result.reports}
    strategy_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for report in result.reports:
        score_by_status[report.status].append(report.quality_score)
        rejection_counts.update(report.rejection_reasons)
    for puzzle in result.candidates:
        status = report_by_id[puzzle.id].status
        strategy_counts[puzzle.source_strategy][status] += 1
    return {
        "summary": {
            "generated": len(result.candidates),
            "automatic_pass": status_counts["publish"] + status_counts["revise"],
            "published": status_counts["publish"],
            "revise": status_counts["revise"],
            "rejected": status_counts["reject"],
            "acceptance_rate": safe_rate(status_counts["publish"], len(result.candidates)),
            "quality_gate": "continue" if status_counts["publish"] >= max(3, int(0.25 * len(result.candidates))) else "needs_review",
            "evidence_level": "automatic_screen_only",
            "human_agreement": None,
        },
        "score_by_status": {
            status: {
                "count": len(scores),
                "mean": round(sum(scores) / len(scores), 2) if scores else 0,
                "min": round(min(scores), 2) if scores else 0,
                "max": round(max(scores), 2) if scores else 0,
            }
            for status, scores in sorted(score_by_status.items())
        },
        "screening_flags": dict(rejection_counts.most_common()),
        "rejection_reasons": dict(rejection_counts.most_common()),
        "strategy_outcomes": {strategy: dict(counter) for strategy, counter in sorted(strategy_counts.items())},
        "top_puzzles": [
            {
                "id": puzzle.id,
                "title": puzzle.title,
                "score": round(report_by_id[puzzle.id].quality_score, 2),
                "theme": puzzle.theme,
                "strategy": puzzle.source_strategy,
            }
            for puzzle in sorted(result.candidates, key=lambda item: report_by_id[item.id].quality_score, reverse=True)[:10]
        ],
        "manual_review": {
            "target_reviews": 50,
            "completed_reviews": 0,
            "labels": {"good": 0, "borderline": 0, "bad": 0},
            "note": "A focused sample screen can be run before treating the bank as final.",
        },
        "evidence_notes": [
            "The current batch is generated by the local template generator for reproducible development.",
            "Published means the candidate passed automatic checks and is eligible for the curated play bank.",
            "Historical reference data is used for near-duplicate checks and mechanism calibration.",
        ],
    }


def safe_rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 3)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
