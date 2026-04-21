"""Validation and heuristic quality scoring for candidate puzzles."""

from __future__ import annotations

from collections import Counter
from statistics import pstdev
from typing import Iterable

from .schema import DIFFICULTIES, Puzzle, QualityReport, ValidationIssue
from .seed_bank import COMMON_WORDS

try:  # Optional; the offline seed bank works without this dependency.
    from wordfreq import zipf_frequency
except ImportError:  # pragma: no cover - optional dependency
    zipf_frequency = None

GENERIC_CATEGORY_WORDS = {"things", "stuff", "words", "misc", "various", "related"}
BLOCKING_CODES = {"word_count", "duplicate_words", "group_count", "group_size", "answer_coverage", "bad_difficulty"}


def validate_puzzle(puzzle: Puzzle) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    normalized_words = puzzle.normalized_words()
    counts = Counter(normalized_words)

    if len(normalized_words) != 16:
        issues.append(ValidationIssue("error", "word_count", "Puzzle must have exactly 16 words."))
    duplicates = sorted(word for word, count in counts.items() if count > 1)
    if duplicates:
        issues.append(ValidationIssue("error", "duplicate_words", f"Duplicate words: {', '.join(duplicates)}."))
    if len(puzzle.groups) != 4:
        issues.append(ValidationIssue("error", "group_count", "Puzzle must have exactly 4 answer groups."))

    answer_words: list[str] = []
    for group in puzzle.groups:
        if len(group.words) != 4:
            issues.append(ValidationIssue("error", "group_size", f"{group.id} must have exactly 4 words."))
        answer_words.extend(group.normalized_words())
        if group.difficulty not in DIFFICULTIES:
            issues.append(ValidationIssue("error", "bad_difficulty", f"{group.id} has invalid difficulty {group.difficulty}."))
        category_tokens = {token.lower().strip("_") for token in group.category.replace("/", " ").split()}
        if len(group.category.strip()) < 4:
            issues.append(ValidationIssue("warning", "weak_category", f"{group.id} category is too short."))
        wordplay_label = group.strategy == "wordplay" and group.category.upper().startswith(("WORDS ENDING", "WORDS WITH"))
        if category_tokens & GENERIC_CATEGORY_WORDS and not wordplay_label:
            issues.append(ValidationIssue("warning", "generic_category", f"{group.id} category may be too generic."))
        if len(group.explanation.strip().split()) < 6:
            issues.append(ValidationIssue("warning", "weak_explanation", f"{group.id} explanation is too thin."))

    if sorted(answer_words) != sorted(normalized_words):
        issues.append(ValidationIssue("error", "answer_coverage", "Answer groups must cover the same 16 words shown to the player."))

    obscure = estimate_obscure_words(normalized_words)
    if obscure:
        issues.append(ValidationIssue("warning", "obscure_words", f"Potentially obscure or awkward words: {', '.join(obscure[:6])}."))

    overlap = detect_surface_ambiguity(puzzle)
    if overlap:
        issues.append(ValidationIssue("warning", "surface_ambiguity", overlap))

    return issues


def score_puzzle(puzzle: Puzzle, nearest_reference: dict | None = None) -> QualityReport:
    issues = validate_puzzle(puzzle)
    issue_codes = {issue.code for issue in issues}
    error_count = sum(1 for issue in issues if issue.severity == "error")
    warning_count = sum(1 for issue in issues if issue.severity == "warning")

    components = {
        "format": 100.0 if error_count == 0 else max(0.0, 70.0 - 20.0 * error_count),
        "clarity": clarity_score(issue_codes),
        "uniqueness": uniqueness_score(nearest_reference),
        "nyt_likeness": nyt_likeness_score(puzzle),
        "difficulty_balance": difficulty_balance_score(puzzle),
        "word_familiarity": familiarity_score(puzzle),
        "explanation_quality": explanation_score(puzzle),
        "ambiguity_penalty": ambiguity_penalty(issue_codes),
        "duplicate_penalty": duplicate_penalty(nearest_reference),
        "obscurity_penalty": min(20.0, warning_count * 2.5),
    }
    positive = (
        0.18 * components["format"]
        + 0.18 * components["clarity"]
        + 0.15 * components["uniqueness"]
        + 0.14 * components["nyt_likeness"]
        + 0.12 * components["difficulty_balance"]
        + 0.11 * components["word_familiarity"]
        + 0.12 * components["explanation_quality"]
    )
    quality = positive - components["ambiguity_penalty"] - components["duplicate_penalty"] - components["obscurity_penalty"]
    quality = max(0.0, min(100.0, quality))

    rejection_reasons = rejection_reasons_for(issues, quality, nearest_reference)
    if issue_codes & BLOCKING_CODES or quality < 65:
        status = "reject"
    elif quality < 82 or warning_count > 2:
        status = "revise"
    else:
        status = "publish"

    return QualityReport(
        puzzle_id=puzzle.id,
        status=status,
        quality_score=quality,
        components=components,
        issues=issues,
        rejection_reasons=rejection_reasons,
        nearest_reference=nearest_reference,
    )


def estimate_obscure_words(words: Iterable[str]) -> list[str]:
    obscure: list[str] = []
    for word in words:
        if word in COMMON_WORDS:
            continue
        if zipf_frequency is not None and zipf_frequency(word.lower(), "en") >= 2.7:
            continue
        if len(word) > 12 or "-" in word or any(ch.isdigit() for ch in word):
            obscure.append(word)
    return obscure


def detect_surface_ambiguity(puzzle: Puzzle) -> str:
    category_tokens_by_group = []
    for group in puzzle.groups:
        tokens = set(group.category.upper().replace("_", " ").replace("/", " ").split())
        tokens |= {token for word in group.words for token in word.upper().split()}
        category_tokens_by_group.append((group.id, tokens))
    overlaps: list[str] = []
    for index, (left_id, left_tokens) in enumerate(category_tokens_by_group):
        for right_id, right_tokens in category_tokens_by_group[index + 1 :]:
            overlap = sorted((left_tokens & right_tokens) - {"WORDS", "THINGS"})
            if len(overlap) >= 2:
                overlaps.append(f"{left_id}/{right_id}: {', '.join(overlap[:4])}")
    if not overlaps:
        return ""
    return "Surface token overlap may create ambiguity: " + "; ".join(overlaps)


def clarity_score(issue_codes: set[str]) -> float:
    score = 94.0
    if "weak_category" in issue_codes:
        score -= 10.0
    if "generic_category" in issue_codes:
        score -= 12.0
    if "weak_explanation" in issue_codes:
        score -= 10.0
    return max(0.0, score)


def uniqueness_score(nearest_reference: dict | None) -> float:
    if not nearest_reference:
        return 92.0
    similarity = float(nearest_reference.get("similarity", 0.0))
    return max(0.0, 100.0 - 85.0 * similarity)


def duplicate_penalty(nearest_reference: dict | None) -> float:
    if not nearest_reference:
        return 0.0
    similarity = float(nearest_reference.get("similarity", 0.0))
    if similarity >= 0.85:
        return 35.0
    if similarity >= 0.65:
        return 18.0
    if similarity >= 0.45:
        return 8.0
    return 0.0


def nyt_likeness_score(puzzle: Puzzle) -> float:
    strategies = [group.strategy for group in puzzle.groups]
    strategy_diversity = len(set(strategies))
    phrase_count = strategies.count("phrase_completion")
    wordplay_count = strategies.count("wordplay")
    score = 76.0 + 6.0 * strategy_diversity
    if 1 <= phrase_count <= 2:
        score += 7.0
    if wordplay_count == 1:
        score += 4.0
    if wordplay_count > 1:
        score -= 10.0
    return max(0.0, min(100.0, score))


def difficulty_balance_score(puzzle: Puzzle) -> float:
    difficulty_values = {"yellow": 1, "green": 2, "blue": 3, "purple": 4}
    values = [difficulty_values.get(group.difficulty, 2) for group in puzzle.groups]
    if len(values) != 4:
        return 60.0
    spread = max(values) - min(values)
    deviation = pstdev(values)
    score = 82.0 + 4.0 * spread - 5.0 * abs(deviation - 1.0)
    if len(set(values)) >= 3:
        score += 6.0
    return max(0.0, min(100.0, score))


def familiarity_score(puzzle: Puzzle) -> float:
    words = puzzle.normalized_words()
    long_words = sum(1 for word in words if len(word) > 10)
    multi_word = sum(1 for word in words if " " in word)
    known = sum(1 for word in words if word in COMMON_WORDS)
    return max(0.0, min(100.0, 72.0 + 1.5 * known - 3.0 * long_words - 2.0 * multi_word))


def explanation_score(puzzle: Puzzle) -> float:
    lengths = [len(group.explanation.split()) for group in puzzle.groups]
    if not lengths:
        return 0.0
    thin = sum(1 for length in lengths if length < 6)
    overly_long = sum(1 for length in lengths if length > 28)
    return max(0.0, min(100.0, 88.0 - 12.0 * thin - 4.0 * overly_long))


def ambiguity_penalty(issue_codes: set[str]) -> float:
    return 7.0 if "surface_ambiguity" in issue_codes else 0.0


def rejection_reasons_for(issues: list[ValidationIssue], quality: float, nearest_reference: dict | None) -> list[str]:
    reasons = [issue.code for issue in issues if issue.severity == "error"]
    reasons.extend(issue.code for issue in issues if issue.severity == "warning")
    if nearest_reference and float(nearest_reference.get("similarity", 0.0)) >= 0.65:
        reasons.append("near_duplicate_reference")
    if quality < 65:
        reasons.append("low_quality_score")
    return sorted(set(reasons))
