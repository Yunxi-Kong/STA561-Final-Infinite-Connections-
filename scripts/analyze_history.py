from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze historical/reference Connections data.")
    parser.add_argument("--reference", type=Path, default=Path("data/history/reference_sets.json"))
    parser.add_argument("--taxonomy", type=Path, default=Path("data/history/mechanism_taxonomy.json"))
    parser.add_argument("--output-json", type=Path, default=Path("data/reports/history_analysis.json"))
    parser.add_argument("--output-md", type=Path, default=Path("reports/history_analysis.md"))
    args = parser.parse_args()

    references = load_references(args.reference)
    taxonomy = load_taxonomy(args.taxonomy)
    analysis = analyze(references, taxonomy)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(analysis, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_markdown(analysis), encoding="utf-8")
    print(f"Analyzed {analysis['summary']['reference_count']} reference records")
    print(f"Wrote {args.output_json}")
    print(f"Wrote {args.output_md}")


def load_references(path: Path) -> list[dict]:
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    data = raw.get("references", raw if isinstance(raw, list) else [])
    references = []
    for index, item in enumerate(data):
        groups = item.get("groups") or item.get("categories") or []
        words = item.get("words") or []
        if groups and not words:
            for group in groups:
                words.extend(group.get("words", []))
        references.append(
            {
                "id": str(item.get("id", f"reference-{index + 1}")),
                "title": str(item.get("title", item.get("date", f"Reference {index + 1}"))),
                "words": [normalize_word(word) for word in words if normalize_word(word)],
                "groups": groups,
            }
        )
    return references


def load_taxonomy(path: Path) -> list[dict]:
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    return list(raw.get("mechanisms", []))


def analyze(references: list[dict], taxonomy: list[dict]) -> dict:
    word_counter: Counter[str] = Counter()
    title_tokens: Counter[str] = Counter()
    size_counter: Counter[int] = Counter()
    mechanism_counter: Counter[str] = Counter()
    for reference in references:
        unique_words = sorted(set(reference["words"]))
        word_counter.update(unique_words)
        size_counter[len(unique_words)] += 1
        title_tokens.update(tokenize(reference["title"]))
        for group in reference.get("groups", []):
            mechanism = classify_mechanism(group)
            mechanism_counter[mechanism] += 1
    if not mechanism_counter:
        mechanism_counter["not_coded_yet"] = len(references)
    return {
        "summary": {
            "reference_count": len(references),
            "unique_word_count": len(word_counter),
            "complete_16_word_records": size_counter.get(16, 0),
            "data_status": "placeholder_reference" if len(references) < 50 else "analysis_ready",
        },
        "mechanism_taxonomy": taxonomy,
        "mechanism_counts": dict(mechanism_counter.most_common()),
        "most_common_words": word_counter.most_common(25),
        "record_size_counts": {str(key): value for key, value in sorted(size_counter.items())},
        "title_tokens": title_tokens.most_common(20),
        "next_data_tasks": next_data_tasks(len(references)),
    }


def next_data_tasks(reference_count: int) -> list[str]:
    if reference_count < 50:
        return [
            "Import full historical puzzle data before using these counts as evidence.",
            "Code each historical group into a mechanism category.",
            "Compare generated candidate mechanism mix against the historical mix.",
            "Use historical word sets for near-duplicate rejection only.",
        ]
    return [
        "Manually audit a sample of mechanism labels because the current taxonomy coding is heuristic.",
        "Compare generated candidate mechanism mix against the historical mix.",
        "Use historical word sets for near-duplicate rejection only.",
        "Add manual review labels and compare them with automatic quality scores.",
    ]


def classify_mechanism(group: dict) -> str:
    label = " ".join(str(group.get(key, "")) for key in ("category", "label", "name", "title")).lower()
    if "___" in label or "blank" in label or "before" in label or "after" in label:
        return "phrase_completion"
    if "homophone" in label or "sound" in label or "rhymes" in label:
        return "homophone_or_sound"
    if "prefix" in label or "suffix" in label or "starts" in label or "ends" in label:
        return "shared_prefix_suffix"
    if "letter" in label or "silent" in label or "palindrome" in label:
        return "spelling_wordplay"
    if "movie" in label or "singer" in label or "actor" in label or "brand" in label:
        return "proper_nouns_culture"
    return "semantic_or_uncoded"


def render_markdown(analysis: dict) -> str:
    summary = analysis["summary"]
    mechanism_lines = "\n".join(f"- {key}: {value}" for key, value in analysis["mechanism_counts"].items())
    word_lines = "\n".join(f"- {word}: {count}" for word, count in analysis["most_common_words"][:12])
    task_lines = "\n".join(f"- {task}" for task in analysis["next_data_tasks"])
    return f"""# Historical Data Analysis

## Status

Reference records analyzed: {summary['reference_count']}

Complete 16-word records: {summary['complete_16_word_records']}

Data status: {summary['data_status']}

The current repository includes a placeholder reference file so the pipeline can run end to end. This page becomes a real evidence section after importing the full historical Connections dataset.

## Mechanism Counts

{mechanism_lines or '- No mechanisms coded yet.'}

## Common Reference Words

{word_lines or '- No reference words loaded yet.'}

## Next Data Tasks

{task_lines}
"""


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in re.findall(r"[A-Za-z]{3,}", text)]


def normalize_word(value: object) -> str:
    return " ".join(str(value).strip().upper().split())


if __name__ == "__main__":
    main()
