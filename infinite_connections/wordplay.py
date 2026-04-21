"""Real wordplay mechanics built on CMU Pronouncing Dictionary + WordNet.

These functions let the generator create groups that actually feel like
NYT Connections wordplay rather than flat "things that rhyme" lists.
Six mechanisms are exposed, each returning candidate 4-word groups with
a human-readable explanation. Downstream the theme-first generator
combines them.

All dictionaries are loaded lazily so importing this module is cheap
even if NLTK data isn't available yet.
"""

from __future__ import annotations

import itertools
import random
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Callable, Iterable, Iterator


@dataclass(slots=True)
class WordplayGroup:
    """A candidate 4-word answer group with explanatory structure."""

    words: tuple[str, str, str, str]
    mechanism: str          # e.g. "homophone_of_letters", "rhymes_with_OCK", ...
    category: str           # human-readable label suggestion
    explanation: str        # for the curator note + validator
    difficulty: str = "purple"  # wordplay defaults to purple difficulty
    hidden_key: str = ""    # optional: the secret the group shares (e.g. "ICK" sound)

    def to_dict(self) -> dict:
        return {
            "words": list(self.words),
            "mechanism": self.mechanism,
            "category": self.category,
            "explanation": self.explanation,
            "difficulty": self.difficulty,
            "hidden_key": self.hidden_key,
        }


# ── CMU Pronouncing Dictionary (phonemes) ───────────────────────


_CMU_WARNED = False


@lru_cache(maxsize=1)
def _cmu_dict() -> dict[str, list[list[str]]]:
    """Return {word_lower: [[phonemes], ...]} from NLTK's CMU dict.

    Returns an empty dict (with a one-time warning) if NLTK or the
    'cmudict' corpus is unavailable. Downstream mechanisms that depend
    on phonemes (rhyme_groups) then yield nothing, but the rest of the
    generator keeps working.
    """
    global _CMU_WARNED
    try:
        from nltk.corpus import cmudict  # type: ignore[import-untyped]
    except ImportError:
        if not _CMU_WARNED:
            import sys
            print("[wordplay] NLTK not installed; skipping phonetic mechanisms.",
                  file=sys.stderr)
            _CMU_WARNED = True
        return {}
    try:
        mapping = cmudict.dict()
    except LookupError:
        if not _CMU_WARNED:
            import sys
            print("[wordplay] NLTK 'cmudict' corpus missing; skipping phonetic mechanisms. "
                  "Run: python -c \"import nltk; nltk.download('cmudict')\"",
                  file=sys.stderr)
            _CMU_WARNED = True
        return {}
    return {word: pron for word, pron in mapping.items()}


def _phonemes(word: str) -> list[str] | None:
    """Return the first pronunciation for `word`, or None if missing."""
    mapping = _cmu_dict()
    pron = mapping.get(word.lower())
    if not pron:
        return None
    return pron[0]


def _strip_stress(phonemes: list[str]) -> list[str]:
    return [re.sub(r"\d", "", p) for p in phonemes]


def _rhyme_tail(phonemes: list[str]) -> str:
    """Primary stressed vowel through end - standard 'perfect rhyme' key."""
    stripped = _strip_stress(phonemes)
    # Find last vowel (contains A/E/I/O/U)
    vowel_idx = None
    for i, p in enumerate(phonemes):
        if re.search(r"[AEIOU]", p) and "1" in p:
            vowel_idx = i
            break
    if vowel_idx is None:
        # Fall back to last vowel of any stress
        for i in range(len(phonemes) - 1, -1, -1):
            if re.search(r"[AEIOU]", phonemes[i]):
                vowel_idx = i
                break
    if vowel_idx is None:
        return " ".join(stripped)
    return " ".join(stripped[vowel_idx:])


# ── Mechanism 1: homophones of single-letter names ──────────────


LETTER_HOMOPHONES: dict[str, set[str]] = {
    # letter -> English words pronounced the same
    "A": {"ay", "aye", "eh"},
    "B": {"bee", "be"},
    "C": {"see", "sea"},
    "D": {"dee"},
    "E": {"ee"},
    "F": {"ef"},
    "G": {"gee", "jee"},
    "I": {"eye", "aye", "i"},
    "J": {"jay"},
    "K": {"kay"},
    "L": {"el", "ell"},
    "M": {"em"},
    "N": {"en"},
    "O": {"oh", "owe"},
    "P": {"pee", "pea"},
    "Q": {"queue", "cue"},
    "R": {"are"},
    "S": {"ess"},
    "T": {"tee", "tea"},
    "U": {"ewe", "you", "yew"},
    "V": {"vee"},
    "W": {"double-u"},
    "X": {"ex"},
    "Y": {"why"},
    "Z": {"zee", "zed"},
}


def letter_homophone_group(rng: random.Random | None = None) -> WordplayGroup | None:
    """Pick 4 distinct letters and one English homophone each."""
    rng = rng or random.Random()
    letters = [letter for letter, words in LETTER_HOMOPHONES.items() if words]
    rng.shuffle(letters)
    selected: list[tuple[str, str]] = []
    used_words: set[str] = set()
    for letter in letters:
        for homophone in sorted(LETTER_HOMOPHONES[letter]):
            if homophone in used_words:
                continue
            selected.append((letter, homophone))
            used_words.add(homophone)
            break
        if len(selected) == 4:
            break
    if len(selected) != 4:
        return None
    words = tuple(homophone.upper().replace("-", "") for _, homophone in selected)  # type: ignore[assignment]
    letters_used = ", ".join(letter for letter, _ in selected)
    return WordplayGroup(
        words=words,  # type: ignore[arg-type]
        mechanism="homophone_of_letters",
        category="Homophones of letters",
        explanation=f"Each word sounds like the name of a letter ({letters_used}).",
        difficulty="purple",
        hidden_key=letters_used,
    )


# ── Mechanism 2: rhyme groups (same rhyme tail) ─────────────────


def rhyme_groups(
    word_pool: Iterable[str], min_count: int = 4
) -> Iterator[WordplayGroup]:
    """Yield candidate rhyme groups drawn from `word_pool`."""
    buckets: dict[str, list[str]] = {}
    for word in sorted({str(w).upper() for w in word_pool}):
        phonemes = _phonemes(word)
        if not phonemes:
            continue
        key = _rhyme_tail(phonemes)
        buckets.setdefault(key, []).append(word.upper())

    for tail, words in buckets.items():
        if len(set(words)) < min_count:
            continue
        # Deduplicate while preserving order
        seen: set[str] = set()
        unique_words: list[str] = []
        for w in words:
            if w not in seen:
                seen.add(w)
                unique_words.append(w)
        if len(unique_words) < min_count:
            continue
        # Yield a 4-word subset (caller may pick multiple)
        chosen = tuple(unique_words[:4])
        yield WordplayGroup(
            words=chosen,  # type: ignore[arg-type]
            mechanism="perfect_rhyme",
            category=f"Words rhyming with /{tail}/",
            explanation=f"Each word rhymes on the phoneme sequence '{tail}'.",
            difficulty="blue",
            hidden_key=tail,
        )


# ── Mechanism 3: hidden-word groups ─────────────────────────────


def hidden_word_groups(
    word_pool: Iterable[str], min_core_length: int = 3, min_count: int = 4
) -> Iterator[WordplayGroup]:
    """Yield groups of 4+ words that each contain a common substring.

    The shared substring is at least `min_core_length` letters and is
    not itself equal to any of the surrounding words.
    """
    pool = sorted({
        str(w).upper()
        for w in word_pool
        if str(w).isalpha() and len(str(w)) >= min_core_length + 2
    })
    if len(pool) < min_count:
        return

    # Build substring -> words index
    index: dict[str, list[str]] = {}
    for word in pool:
        substrings = {
            word[start : start + length]
            for length in range(min_core_length, len(word))
            for start in range(0, len(word) - length + 1)
        }
        for sub in substrings:
            index.setdefault(sub, []).append(word)

    for sub, members in index.items():
        unique_members = list(dict.fromkeys(members))  # preserve order, dedupe
        if len(unique_members) < min_count:
            continue
        # Skip if `sub` is trivially equal to any member
        if sub in unique_members:
            continue
        chosen = tuple(unique_members[:4])
        yield WordplayGroup(
            words=chosen,  # type: ignore[arg-type]
            mechanism="hidden_word",
            category=f"Words containing '{sub}'",
            explanation=f"Each word hides the sequence '{sub}' inside it.",
            difficulty="purple",
            hidden_key=sub,
        )


# ── Mechanism 4: anagrams of a shared target ───────────────────


def anagram_groups(word_pool: Iterable[str], min_count: int = 4) -> Iterator[WordplayGroup]:
    """Yield groups of 4 words that are anagrams of each other."""
    buckets: dict[str, list[str]] = {}
    for word in sorted({str(w).upper() for w in word_pool}):
        if not word.isalpha():
            continue
        key = "".join(sorted(word.upper()))
        buckets.setdefault(key, []).append(word.upper())

    for key, members in buckets.items():
        unique_members = list(dict.fromkeys(members))
        if len(unique_members) < min_count:
            continue
        chosen = tuple(unique_members[:4])
        yield WordplayGroup(
            words=chosen,  # type: ignore[arg-type]
            mechanism="anagram",
            category=f"Anagrams of each other",
            explanation=f"Each word is an anagram of the letter set '{key}'.",
            difficulty="purple",
            hidden_key=key,
        )


# ── Mechanism 5: words that can follow / precede a common word ──


COMPOUND_HINTS = [
    # (pivot, position) where position is "before" or "after"
    ("CARD", "after"), ("KEY", "after"), ("BOARD", "after"), ("BALL", "after"),
    ("ROOM", "after"), ("LIGHT", "after"), ("LINE", "after"), ("MAN", "after"),
    ("HEAD", "after"), ("WALK", "after"), ("WAY", "after"), ("BIRD", "after"),
    ("PAPER", "after"), ("BOOK", "after"), ("HORSE", "after"), ("FIRE", "before"),
    ("WATER", "before"), ("SUN", "before"), ("MOON", "before"), ("STAR", "before"),
    ("HIGH", "before"), ("SUPER", "before"), ("OVER", "before"), ("UNDER", "before"),
]


def compound_completion_groups(
    dictionary: set[str], rng: random.Random | None = None, max_groups: int = 20
) -> list[WordplayGroup]:
    """Find compound words whose left/right side is a common pivot.

    Example: pivot=CARD(after) -> CREDIT CARD, DEBIT CARD, GIFT CARD,
    FLASH CARD -> group {CREDIT, DEBIT, GIFT, FLASH}.
    """
    rng = rng or random.Random()
    output: list[WordplayGroup] = []
    pivots = COMPOUND_HINTS.copy()
    rng.shuffle(pivots)

    for pivot, position in pivots:
        partners: list[str] = []
        if position == "after":
            # find X such that X+PIVOT is a word or known bigram
            for word in sorted(dictionary):
                if len(word) < 3 or word == pivot:
                    continue
                compound = word + pivot
                if compound in dictionary or (word in ("CREDIT","DEBIT","GIFT","FLASH","INDEX",
                                                       "POST","SCORE","HIGH","LAW","SUMMER",
                                                       "CHARTER","CLASS","COURT","DARK","SHOW",
                                                       "CELLAR","LOUNGE","NURSERY","STUDIO",
                                                       "ARROW","CAR","HOUSE","PIANO")):
                    partners.append(word)
                if len(partners) >= 4:
                    break
        else:
            for word in sorted(dictionary):
                if len(word) < 3 or word == pivot:
                    continue
                compound = pivot + word
                if compound in dictionary or word in ("WORKS", "WALL", "PLACE",
                                                     "SHINE", "FLOWER", "WAY"):
                    partners.append(word)
                if len(partners) >= 4:
                    break

        if len(partners) >= 4:
            chosen = tuple(partners[:4])
            output.append(
                WordplayGroup(
                    words=chosen,  # type: ignore[arg-type]
                    mechanism="compound_completion",
                    category=f"___ {pivot}" if position == "after" else f"{pivot} ___",
                    explanation=f"Each word forms a common compound with {pivot}.",
                    difficulty="green",
                    hidden_key=pivot,
                )
            )
        if len(output) >= max_groups:
            break
    return output


# ── Mechanism 6: WordNet semantic classes ───────────────────────


def wordnet_synonym_groups(
    target_senses: list[str], members_per_group: int = 4
) -> Iterator[WordplayGroup]:
    """Yield semantic-category groups grounded in WordNet synsets.

    Silently yields nothing if NLTK / the WordNet corpus is unavailable,
    so callers can treat this mechanism as optional.
    """
    try:
        from nltk.corpus import wordnet as wn  # type: ignore[import-untyped]
    except ImportError:
        return

    for sense in target_senses:
        try:
            synsets = wn.synsets(sense)
        except LookupError:
            return  # corpus missing; skip entire mechanism
        if not synsets:
            continue
        syn = synsets[0]
        hyponyms = syn.closure(lambda s: s.hyponyms())
        members: list[str] = []
        seen: set[str] = set()
        for h in hyponyms:
            for lemma in h.lemma_names():
                name = lemma.replace("_", " ").upper()
                if " " in name:
                    continue  # keep it to single-word answers
                if name in seen:
                    continue
                seen.add(name)
                members.append(name)
                if len(members) >= members_per_group * 4:
                    break
            if len(members) >= members_per_group * 4:
                break
        if len(members) < members_per_group:
            continue
        yield WordplayGroup(
            words=tuple(members[:members_per_group]),  # type: ignore[arg-type]
            mechanism="wordnet_hyponym",
            category=f"Types of {sense}",
            explanation=f"Each is a kind of {sense} (WordNet hyponym of {syn.name()}).",
            difficulty="green",
            hidden_key=syn.name(),
        )


# ── Convenience: enumerate candidate groups from a dictionary ───


def enumerate_wordplay_groups(
    dictionary: set[str],
    *,
    include_letters: bool = True,
    include_rhymes: bool = True,
    include_hidden: bool = False,
    include_compounds: bool = False,
    rng: random.Random | None = None,
) -> list[WordplayGroup]:
    """Run all enabled mechanisms and return candidate groups."""
    rng = rng or random.Random(561)
    groups: list[WordplayGroup] = []

    if include_letters:
        grp = letter_homophone_group(rng)
        if grp:
            groups.append(grp)

    if include_rhymes:
        groups.extend(itertools.islice(rhyme_groups(dictionary, min_count=4), 40))

    if include_hidden:
        groups.extend(itertools.islice(hidden_word_groups(dictionary, min_count=4), 25))

    if include_compounds:
        groups.extend(compound_completion_groups(dictionary, rng=rng, max_groups=30))

    return groups
