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

from infinite_connections.history import load_reference_sets
from infinite_connections.seed_bank import CATEGORY_BANK

try:
    from wordfreq import zipf_frequency
except ImportError:  # pragma: no cover - optional dependency
    zipf_frequency = None


def main() -> None:
    parser = argparse.ArgumentParser(description="Export the offline answer bank and word inventory caches.")
    parser.add_argument("--reference", type=Path, default=Path("data/history/reference_sets.json"))
    parser.add_argument("--lexicon-dir", type=Path, default=Path("data/lexicons"))
    parser.add_argument("--report", type=Path, default=Path("data/reports/improvement_2_lexicon_cache.json"))
    args = parser.parse_args()

    args.lexicon_dir.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)

    references = load_reference_sets(args.reference)
    answer_bank = build_answer_bank()
    word_inventory = build_word_inventory(answer_bank, references)
    report = build_report(answer_bank, word_inventory, references)

    write_json(args.lexicon_dir / "offline_answer_bank.json", answer_bank)
    write_json(args.lexicon_dir / "word_inventory.json", word_inventory)
    write_json(args.report, report)

    print(f"Exported {len(answer_bank)} answer groups to {args.lexicon_dir / 'offline_answer_bank.json'}")
    print(f"Unique answer-bank words: {report['answer_bank']['unique_words']}")
    print(f"Historical reference records: {report['historical_reference']['records']}")
    print(f"Wrote {args.report}")


def build_answer_bank() -> list[dict[str, Any]]:
    rows = []
    seen: set[tuple[str, ...]] = set()
    for index, template in enumerate(CATEGORY_BANK, start=1):
        signature = tuple(sorted(template.words))
        if signature in seen:
            continue
        seen.add(signature)
        rows.append(
            {
                "id": f"group-{index:05d}",
                "category": template.category,
                "words": list(template.words),
                "difficulty": template.difficulty,
                "strategy": template.strategy,
                "explanation": template.explanation,
                "signature": list(signature),
                "source": "offline_seed_bank",
            }
        )
    return rows


def build_word_inventory(answer_bank: list[dict[str, Any]], references: list[dict[str, Any]]) -> dict[str, Any]:
    answer_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()
    history_counts: Counter[str] = Counter()
    for row in answer_bank:
        answer_counts.update(str(word).upper() for word in row["words"])
        category_counts[str(row["category"])] += 1
    for reference in references:
        history_counts.update(str(word).upper() for word in reference.get("words", []))

    words = sorted(set(answer_counts) | set(history_counts))
    return {
        "metadata": {
            "wordfreq_available": zipf_frequency is not None,
            "answer_bank_group_count": len(answer_bank),
            "historical_reference_count": len(references),
        },
        "words": [
            {
                "word": word,
                "answer_bank_count": answer_counts[word],
                "history_count": history_counts[word],
                "zipf_frequency": round(zipf_frequency(word.lower(), "en"), 3) if zipf_frequency else None,
            }
            for word in words
        ],
        "top_answer_bank_words": answer_counts.most_common(50),
        "top_history_words": history_counts.most_common(50),
        "top_categories": category_counts.most_common(50),
    }


def build_report(
    answer_bank: list[dict[str, Any]],
    word_inventory: dict[str, Any],
    references: list[dict[str, Any]],
) -> dict[str, Any]:
    strategy_counts = Counter(row["strategy"] for row in answer_bank)
    category_counts = Counter(row["category"] for row in answer_bank)
    words = {word for row in answer_bank for word in row["words"]}
    history_words = {word for reference in references for word in reference.get("words", [])}
    repeated_groups = len(answer_bank) - len({tuple(row["signature"]) for row in answer_bank})
    return {
        "improvement": "Improvement 2",
        "purpose": "Export a large offline answer-bank cache so large generator runs do not rely on live APIs.",
        "answer_bank": {
            "exact_groups": len(answer_bank),
            "unique_words": len(words),
            "unique_categories": len(category_counts),
            "duplicate_exact_groups": repeated_groups,
            "strategy_counts": dict(strategy_counts),
            "top_categories": category_counts.most_common(20),
        },
        "historical_reference": {
            "records": len(references),
            "unique_words": len(history_words),
            "use": "near-duplicate checks and mechanism calibration only",
        },
        "word_inventory": word_inventory["metadata"],
        "sources": [
            "offline_seed_bank",
            "data/history/reference_sets.json",
            "wordfreq package when installed",
        ],
    }


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
