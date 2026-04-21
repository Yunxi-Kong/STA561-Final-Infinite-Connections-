from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.request import urlopen


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize external Connections history data into reference_sets.json.")
    parser.add_argument("--source", required=True, help="Local JSON file or URL containing historical Connections records.")
    parser.add_argument("--output", type=Path, default=Path("data/history/reference_sets.json"))
    args = parser.parse_args()

    raw = read_json(args.source)
    records = normalize_records(raw)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            {
                "notes": "Historical/reference data for duplicate checks and mechanism analysis. Do not publish copied historical puzzles as generated output.",
                "references": records,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Imported {len(records)} records into {args.output}")


def read_json(source: str):
    if source.startswith(("http://", "https://")):
        with urlopen(source, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    return json.loads(Path(source).read_text(encoding="utf-8"))


def normalize_records(raw) -> list[dict]:
    candidates = raw
    if isinstance(raw, dict):
        for key in ("references", "puzzles", "data", "items", "train"):
            if isinstance(raw.get(key), list):
                candidates = raw[key]
                break
    if not isinstance(candidates, list):
        raise ValueError("Could not find a list of puzzle records in the source JSON.")
    records = []
    for index, item in enumerate(candidates):
        if not isinstance(item, dict):
            continue
        groups = item.get("groups") or item.get("answers") or item.get("categories") or item.get("solution") or []
        words = item.get("words") or item.get("starting_words") or item.get("board") or []
        normalized_groups = normalize_groups(groups)
        if not words and normalized_groups:
            words = [word for group in normalized_groups for word in group["words"]]
        words = unique_words(words)
        if len(words) < 4:
            continue
        records.append(
            {
                "id": str(item.get("id", item.get("date", f"history-{index + 1}"))),
                "title": str(item.get("title", item.get("date", f"Historical puzzle {index + 1}"))),
                "words": words,
                "groups": normalized_groups,
            }
        )
    return records


def normalize_groups(groups) -> list[dict]:
    if isinstance(groups, dict):
        groups = list(groups.values())
    if not isinstance(groups, list):
        return []
    normalized = []
    for index, group in enumerate(groups):
        if isinstance(group, list):
            normalized.append({"category": f"Group {index + 1}", "words": unique_words(group)})
            continue
        if not isinstance(group, dict):
            continue
        words = group.get("words") or group.get("members") or group.get("answers") or group.get("cards") or []
        category = group.get("category") or group.get("group") or group.get("label") or group.get("name") or group.get("title") or f"Group {index + 1}"
        normalized.append({"category": str(category), "words": unique_words(words), "level": group.get("level")})
    return normalized


def unique_words(words) -> list[str]:
    seen = set()
    result = []
    for word in words if isinstance(words, list) else []:
        normalized = " ".join(str(word).strip().upper().split())
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


if __name__ == "__main__":
    main()
