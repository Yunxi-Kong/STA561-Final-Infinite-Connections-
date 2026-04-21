"""Build a unified historical NYT Connections corpus.

Merges three sources into one on-disk dataset of deduplicated real NYT
Connections puzzles, which is the ground-truth anchor for our plausibility
scoring:

  A) data/history/reference_sets.json    (already present, 830 records)
  B) HuggingFace: eric27n/NYT-Connections (Apache-2.0, largest)
  C) GitHub: lechmazur/nyt-connections  (940 puzzles as of early 2026)

Output:
  data/history/unified_reference.json    (list of canonicalised puzzles)
  data/history/unified_summary.json      (counts, dedup stats, date range)

Each record has this schema (matches infinite_connections.schema.Puzzle
but with source provenance):

  {
    "id":        "nyt-YYYY-MM-DD" | "lechmazur-###",
    "date":      "YYYY-MM-DD" | null,
    "words":     [16 UPPER],
    "groups":    [{"category": "...", "words": [4 UPPER], "difficulty": "yellow|green|blue|purple"}, ...],
    "_source":   "eric27n" | "lechmazur" | "local_reference"
  }

Usage on your Windows box:

    python scripts/download_nyt_corpus.py
    python scripts/download_nyt_corpus.py --skip-hf      # only use local + offline caches
    python scripts/download_nyt_corpus.py --skip-github  # skip lechmazur clone
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
HISTORY_DIR = ROOT / "data" / "history"
HF_CACHE_DIR = HISTORY_DIR / "hf_cache"
GITHUB_CACHE_DIR = HISTORY_DIR / "lechmazur_cache"
UNIFIED_PATH = HISTORY_DIR / "unified_reference.json"
SUMMARY_PATH = HISTORY_DIR / "unified_summary.json"


# ── Source readers ─────────────────────────────────────────────


def read_local_reference() -> list[dict]:
    """Read the existing 830-record reference set shipped with the repo."""
    path = HISTORY_DIR / "reference_sets.json"
    if not path.exists():
        print("[local] reference_sets.json missing, skipping.")
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        items = raw
    else:
        # The original project stores its shipped corpus under
        # "references"; some public dumps use "puzzles".  Accept both so
        # the historical-overlap guard cannot silently degrade to zero.
        items = raw.get("references") or raw.get("puzzles") or []
    canonical = []
    for item in items:
        record = _canonicalise_local(item)
        if record:
            record["_source"] = "local_reference"
            canonical.append(record)
    print(f"[local] {len(canonical)} puzzles loaded.")
    return canonical


def _canonicalise_local(item: dict) -> dict | None:
    words = item.get("words") or []
    groups = item.get("groups") or item.get("answers") or []
    if len(words) != 16 or len(groups) != 4:
        return None
    canonical_groups = []
    for g in groups:
        w = g.get("words") or []
        if len(w) != 4:
            return None
        canonical_groups.append({
            "category": str(g.get("category") or g.get("label") or g.get("name") or ""),
            "words": [str(x).upper() for x in w],
            "difficulty": _coerce_difficulty(g.get("difficulty") or g.get("level")),
        })
    return {
        "id": str(item.get("id") or item.get("date") or f"local-{hash(tuple(sorted(words)))}"),
        "date": item.get("date"),
        "words": [str(w).upper() for w in words],
        "groups": canonical_groups,
    }


def read_huggingface() -> list[dict]:
    """Stream eric27n/NYT-Connections from HF and assemble per-puzzle records."""
    try:
        from datasets import load_dataset  # type: ignore[import-untyped]
    except ImportError:
        print("[hf] `datasets` not installed; run setup_env.py first.")
        return []
    print("[hf] Loading eric27n/NYT-Connections (first time will cache to ~/.cache/huggingface/)...")
    try:
        # Avoid project-local cache paths on Windows: Chinese characters and
        # long lock-file names can trip filelock.  Let Hugging Face use the
        # user cache unless the caller explicitly overrides it.
        cache_dir = os.getenv("HF_DATASETS_CACHE") or None
        kwargs = {"cache_dir": cache_dir} if cache_dir else {}
        ds = load_dataset("eric27n/NYT-Connections", split="train", **kwargs)
    except Exception as exc:
        print(f"[hf] Failed to load dataset: {exc.__class__.__name__}")
        return []

    # eric27n/NYT-Connections is stored as one row per (game, word).
    # Column names vary slightly between dumps; we detect them at runtime.
    rows = [dict(row) for row in ds]
    if not rows:
        return []

    sample = rows[0]
    game_id_key = _first_present_key(sample, ["Game ID", "game_id", "GameID", "id"])
    date_key = _first_present_key(sample, ["Puzzle Date", "puzzle_date", "date"])
    word_key = _first_present_key(sample, ["Word", "word"])
    group_key = _first_present_key(sample, ["Group Name", "group_name", "category", "Group"])
    difficulty_key = _first_present_key(sample, ["Group Level", "group_level", "difficulty"])

    if None in (game_id_key, word_key, group_key):
        print(f"[hf] Unexpected schema; columns were {list(sample.keys())}")
        return []

    # Group by puzzle
    by_puzzle: dict[str, dict] = {}
    for row in rows:
        pid = str(row.get(game_id_key))
        puzzle = by_puzzle.setdefault(pid, {
            "id": f"eric27n-{pid}",
            "date": row.get(date_key) if date_key else None,
            "words": [],
            "_raw_groups": {},
        })
        word = str(row.get(word_key, "")).upper()
        group_name = str(row.get(group_key, ""))
        difficulty_val = row.get(difficulty_key) if difficulty_key else None
        if word:
            puzzle["words"].append(word)
        bucket = puzzle["_raw_groups"].setdefault(group_name, {
            "category": group_name,
            "words": [],
            "difficulty": _coerce_difficulty(difficulty_val),
        })
        bucket["words"].append(word)

    canonical = []
    for puzzle in by_puzzle.values():
        groups = list(puzzle["_raw_groups"].values())
        if len(groups) != 4 or len(puzzle["words"]) != 16:
            continue
        if any(len(g["words"]) != 4 for g in groups):
            continue
        canonical.append({
            "id": puzzle["id"],
            "date": puzzle["date"],
            "words": puzzle["words"],
            "groups": [{
                "category": g["category"],
                "words": g["words"],
                "difficulty": g["difficulty"],
            } for g in groups],
            "_source": "eric27n",
        })
    print(f"[hf] {len(canonical)} puzzles assembled.")
    return canonical


def read_lechmazur() -> list[dict]:
    """Clone lechmazur/nyt-connections and read puzzles.json or equivalent."""
    if not shutil_which("git"):
        print("[lechmazur] git not found on PATH; skipping.")
        return []
    GITHUB_CACHE_DIR.parent.mkdir(parents=True, exist_ok=True)
    target = GITHUB_CACHE_DIR / "lechmazur-nyt-connections"
    if not target.exists():
        print("[lechmazur] Cloning repo (shallow)...")
        rc = subprocess.run(
            ["git", "clone", "--depth", "1",
             "https://github.com/lechmazur/nyt-connections.git", str(target)],
            capture_output=True,
        ).returncode
        if rc != 0:
            print("[lechmazur] Clone failed; skipping.")
            return []
    else:
        subprocess.run(["git", "-C", str(target), "pull", "--depth", "1"], capture_output=True)

    # The repo uses puzzle_NNNN.txt or a consolidated JSON; we prefer JSON.
    consolidated = None
    for candidate in ("puzzles.json", "connections.json", "all_puzzles.json"):
        path = target / candidate
        if path.exists():
            consolidated = path
            break

    canonical: list[dict] = []
    if consolidated and consolidated.exists():
        try:
            payload = json.loads(consolidated.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = []
        iterable = payload if isinstance(payload, list) else payload.get("puzzles", [])
        for item in iterable:
            record = _canonicalise_lechmazur(item)
            if record:
                record["_source"] = "lechmazur"
                canonical.append(record)
    else:
        # Fallback: scan individual puzzle_*.txt files
        for txt_path in sorted(target.rglob("puzzle_*.txt")):
            record = _parse_lechmazur_txt(txt_path)
            if record:
                record["_source"] = "lechmazur"
                canonical.append(record)
    print(f"[lechmazur] {len(canonical)} puzzles loaded.")
    return canonical


def _canonicalise_lechmazur(item: dict) -> dict | None:
    words = item.get("words") or item.get("board") or []
    groups = item.get("groups") or item.get("solutions") or []
    if len(words) != 16 or len(groups) != 4:
        return None
    canonical_groups = []
    for g in groups:
        w = g.get("words") or g.get("answers") or []
        if len(w) != 4:
            return None
        canonical_groups.append({
            "category": str(g.get("category") or g.get("label") or g.get("name") or ""),
            "words": [str(x).upper() for x in w],
            "difficulty": _coerce_difficulty(g.get("difficulty") or g.get("level")),
        })
    return {
        "id": str(item.get("id") or item.get("date") or f"lechmazur-{hash(tuple(sorted(words)))}"),
        "date": item.get("date"),
        "words": [str(w).upper() for w in words],
        "groups": canonical_groups,
    }


def _parse_lechmazur_txt(path: Path) -> dict | None:
    """Minimal text-format parser; ignore files that don't match."""
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return None
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    # Not implemented in detail here; the JSON path handles the bulk case.
    # If your local clone stores puzzles as JSON inside this file, parse it here.
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return None
    return _canonicalise_lechmazur(data)


# ── Helpers ─────────────────────────────────────────────────────


def _coerce_difficulty(value) -> str:
    if value is None:
        return "green"
    s = str(value).strip().lower()
    if s in ("yellow", "green", "blue", "purple"):
        return s
    # eric27n dataset uses numeric 0-3 where 0=yellow ... 3=purple
    mapping = {"0": "yellow", "1": "green", "2": "blue", "3": "purple"}
    return mapping.get(s, "green")


def _first_present_key(row: dict, candidates: list[str]) -> str | None:
    for key in candidates:
        if key in row:
            return key
    return None


def shutil_which(binary: str) -> str | None:
    import shutil
    return shutil.which(binary)


# ── Dedup + merge ──────────────────────────────────────────────


def canonical_signature(puzzle: dict) -> tuple[str, ...]:
    """Sorted lowercase words, stable for exact-duplicate detection."""
    return tuple(sorted(w.strip().upper() for w in puzzle["words"]))


def merge_all(sources: list[list[dict]]) -> tuple[list[dict], dict[str, int]]:
    seen: dict[tuple[str, ...], dict] = {}
    counts: dict[str, int] = {"duplicates": 0}
    for source in sources:
        for puzzle in source:
            sig = canonical_signature(puzzle)
            if sig in seen:
                counts["duplicates"] += 1
                continue
            seen[sig] = puzzle
            counts.setdefault(puzzle.get("_source", "unknown"), 0)
            counts[puzzle.get("_source", "unknown")] += 1
    return list(seen.values()), counts


# ── CLI ─────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-hf", action="store_true")
    parser.add_argument("--skip-github", action="store_true")
    args = parser.parse_args()

    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    sources: list[list[dict]] = [read_local_reference()]
    if not args.skip_hf:
        sources.append(read_huggingface())
    if not args.skip_github:
        sources.append(read_lechmazur())

    unified, counts = merge_all(sources)
    UNIFIED_PATH.write_text(json.dumps(unified, indent=2), encoding="utf-8")

    dates = [p.get("date") for p in unified if p.get("date")]
    summary = {
        "count": len(unified),
        "source_counts": counts,
        "date_min": min(dates) if dates else None,
        "date_max": max(dates) if dates else None,
        "output_path": str(UNIFIED_PATH.relative_to(ROOT)),
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nUnified corpus: {summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
