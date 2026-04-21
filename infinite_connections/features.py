"""Puzzle-level feature extraction for distributional plausibility scoring.

Each puzzle is represented as a fixed-length feature vector that captures
properties every NYT Connections regular would notice: word length, word
frequency, part-of-speech mix, category-label shape, intra-group
embedding cohesion, inter-group separation, phonetic density, etc.

We compute the same vector for our generated puzzles and for the 1400+
historical NYT puzzles, then:

  1. compare distributions with KL divergence / Wasserstein distance;
  2. train a light NYT-likeness classifier (logistic regression or
     XGBoost) on these vectors.

The features are intentionally interpretable so the technical appendix
can explain each one in a paragraph.
"""

from __future__ import annotations

import re
import statistics
from dataclasses import dataclass
from typing import Any, Iterable

import numpy as np


FEATURE_NAMES: list[str] = [
    "word_len_mean",
    "word_len_std",
    "word_len_min",
    "word_len_max",
    "word_freq_mean_zipf",
    "word_freq_std_zipf",
    "word_unique_ratio",
    "single_token_ratio",
    "category_len_mean",
    "category_len_std",
    "category_has_blank_ratio",   # "___ X" pattern
    "category_has_apostrophe_ratio",
    "strategy_semantic",
    "strategy_phrase_completion",
    "strategy_wordplay",
    "strategy_other",
    "difficulty_yellow",
    "difficulty_green",
    "difficulty_blue",
    "difficulty_purple",
    "intra_group_sim_mean",       # avg cosine sim within groups (needs embeddings)
    "intra_group_sim_min",
    "inter_group_sim_mean",
    "group_separation",           # intra - inter (higher = cleaner partition)
    "phonetic_density",           # fraction of board words sharing a rhyme tail
]


# ── Public API ─────────────────────────────────────────────────


@dataclass(slots=True)
class FeatureVector:
    puzzle_id: str
    values: list[float]
    source: str  # "nyt" or "generated"

    def as_array(self) -> np.ndarray:
        return np.asarray(self.values, dtype=np.float64)


def extract_features(
    puzzle_dict: dict,
    *,
    embeddings_fn=None,           # callable(words) -> np.ndarray, or None
    rhyme_tail_fn=None,           # callable(word) -> str|None
    zipf_fn=None,                 # callable(word) -> float, uses wordfreq if None
) -> FeatureVector:
    """Compute the full feature vector for one puzzle dict."""

    words = [w for w in puzzle_dict.get("words", [])]
    groups = puzzle_dict.get("groups", [])
    if len(words) != 16 or len(groups) != 4:
        raise ValueError(f"Puzzle {puzzle_dict.get('id','?')} does not have 16 words / 4 groups")

    word_lens = [len(w) for w in words]
    zipf = zipf_fn or _default_zipf
    freqs = [zipf(w) for w in words]

    categories = [str(g.get("category", "") or g.get("label", "") or "") for g in groups]
    strategies = [
        _strategy_from_group(g)
        for g in groups
    ]
    difficulties = [str(g.get("difficulty", "") or "").lower() for g in groups]

    # Embedding-derived features (optional)
    if embeddings_fn is not None:
        vectors = embeddings_fn(words)
        sim = vectors @ vectors.T
        intra, inter, intra_min = _group_similarity_stats(groups, words, sim)
    else:
        intra = inter = intra_min = 0.0

    phonetic_density = _phonetic_density(words, rhyme_tail_fn) if rhyme_tail_fn else 0.0

    features = [
        float(statistics.mean(word_lens)),
        float(statistics.pstdev(word_lens) if len(word_lens) > 1 else 0.0),
        float(min(word_lens)),
        float(max(word_lens)),
        float(statistics.mean(freqs)),
        float(statistics.pstdev(freqs) if len(freqs) > 1 else 0.0),
        float(len({w.upper() for w in words}) / 16.0),
        float(sum(1 for w in words if " " not in w) / 16.0),
        float(statistics.mean([len(c) for c in categories])) if categories else 0.0,
        float(statistics.pstdev([len(c) for c in categories])) if len(categories) > 1 else 0.0,
        float(sum(1 for c in categories if "___" in c or "_ " in c) / 4.0),
        float(sum(1 for c in categories if "'" in c) / 4.0),
        float(sum(1 for s in strategies if s.startswith("semantic")) / 4.0),
        float(sum(1 for s in strategies if "phrase" in s) / 4.0),
        float(sum(1 for s in strategies if "wordplay" in s or "rhyme" in s or "anagram" in s or "hidden" in s) / 4.0),
        float(sum(1 for s in strategies if s and not any(tok in s for tok in ("semantic","phrase","wordplay","rhyme","anagram","hidden"))) / 4.0),
        float(sum(1 for d in difficulties if d == "yellow") / 4.0),
        float(sum(1 for d in difficulties if d == "green") / 4.0),
        float(sum(1 for d in difficulties if d == "blue") / 4.0),
        float(sum(1 for d in difficulties if d == "purple") / 4.0),
        float(intra),
        float(intra_min),
        float(inter),
        float(intra - inter),
        float(phonetic_density),
    ]
    return FeatureVector(
        puzzle_id=str(puzzle_dict.get("id", "unknown")),
        values=features,
        source=str(puzzle_dict.get("_source", "unknown")),
    )


def extract_features_batch(
    puzzle_dicts: Iterable[dict],
    **kwargs,
) -> list[FeatureVector]:
    return [extract_features(p, **kwargs) for p in puzzle_dicts]


def distribution_distance(
    a_vectors: list[FeatureVector], b_vectors: list[FeatureVector]
) -> dict[str, Any]:
    """Compare two sets of feature vectors.

    Returns per-feature Wasserstein-1 distance plus overall mean. Scipy
    is optional; if missing, we fall back to per-feature mean absolute
    deviation, which is good enough for a quick sanity check.
    """
    if not a_vectors or not b_vectors:
        return {"overall": float("nan"), "per_feature": {}}

    a = np.vstack([v.as_array() for v in a_vectors])
    b = np.vstack([v.as_array() for v in b_vectors])

    try:
        from scipy.stats import wasserstein_distance  # type: ignore[import-untyped]
        per_feature = {
            name: float(wasserstein_distance(a[:, i], b[:, i]))
            for i, name in enumerate(FEATURE_NAMES)
        }
    except ImportError:
        per_feature = {
            name: float(abs(a[:, i].mean() - b[:, i].mean()))
            for i, name in enumerate(FEATURE_NAMES)
        }

    return {
        "overall": float(np.mean(list(per_feature.values()))),
        "per_feature": per_feature,
        "a_count": len(a_vectors),
        "b_count": len(b_vectors),
    }


# ── Internals ───────────────────────────────────────────────────


def _default_zipf(word: str) -> float:
    try:
        from wordfreq import zipf_frequency  # type: ignore[import-untyped]
    except ImportError:
        return 3.0  # neutral fallback
    return float(zipf_frequency(word.lower(), "en"))


def _strategy_from_group(group: dict) -> str:
    explicit = str(group.get("strategy", "") or "").lower().strip()
    if explicit:
        return explicit
    category = str(group.get("category", "") or group.get("label", "") or "").upper()
    if "___" in category or category.startswith("_") or category.endswith("_"):
        return "phrase_completion"
    wordplay_terms = (
        "HOMOPHONE",
        "PALINDROME",
        "RHYME",
        "RHYMING",
        "SILENT",
        "LETTER",
        "ENDING",
        "BEGINNING",
        "START",
        "CONTAIN",
        "SOUND",
        "ANAGRAM",
        "PREFIX",
        "SUFFIX",
    )
    if any(term in category for term in wordplay_terms):
        return "wordplay"
    return "semantic"


def _group_similarity_stats(
    groups: list[dict], board_words: list[str], sim: np.ndarray
) -> tuple[float, float, float]:
    index = {w.upper(): i for i, w in enumerate(board_words)}
    intra_means: list[float] = []
    intra_mins: list[float] = []
    for group in groups:
        indices = [index[w.upper()] for w in group.get("words", []) if w.upper() in index]
        if len(indices) < 2:
            continue
        pairs = []
        for i in range(len(indices)):
            for j in range(i + 1, len(indices)):
                pairs.append(float(sim[indices[i], indices[j]]))
        if pairs:
            intra_means.append(sum(pairs) / len(pairs))
            intra_mins.append(min(pairs))

    # inter: pairs across different groups
    inter_pairs: list[float] = []
    group_sets = []
    for group in groups:
        indices = [index[w.upper()] for w in group.get("words", []) if w.upper() in index]
        group_sets.append(indices)
    for i in range(len(group_sets)):
        for j in range(i + 1, len(group_sets)):
            for a in group_sets[i]:
                for b in group_sets[j]:
                    inter_pairs.append(float(sim[a, b]))

    intra_mean = float(statistics.mean(intra_means)) if intra_means else 0.0
    intra_min = float(min(intra_mins)) if intra_mins else 0.0
    inter_mean = float(statistics.mean(inter_pairs)) if inter_pairs else 0.0
    return intra_mean, inter_mean, intra_min


def _phonetic_density(words: list[str], tail_fn) -> float:
    tails: list[str] = []
    for word in words:
        try:
            tail = tail_fn(word)
        except Exception:
            tail = None
        if tail:
            tails.append(tail)
    if not tails:
        return 0.0
    # Fraction of pairs sharing the same tail
    matches = 0
    total = 0
    for i in range(len(tails)):
        for j in range(i + 1, len(tails)):
            total += 1
            if tails[i] == tails[j]:
                matches += 1
    return matches / max(1, total)
