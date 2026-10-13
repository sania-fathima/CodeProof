"""Token-shingle Jaccard baseline plus token-sequence comparison.

Deterministic: no randomness, no wall-clock input, no hash-seed
dependence (shingles are stored as ``tuple`` objects, never hashed for
ordering). Scores are always in ``[0, 1]``.

Limitations (documented for integrators):
- Token-based similarity detects surface overlap, not semantics. Renamed
  identifiers, reordered blocks, or translated logic can raise or lower
  scores without changing program behavior.
- Boilerplate (imports, ``main`` wrappers) inflates scores; see
  :mod:`codeproof_detector.comparison` for boilerplate flagging.
- Short programs yield unstable scores; callers receive a warning.
- A high score is an indicator of overlap, never proof of plagiarism.
"""

from __future__ import annotations

import difflib
from typing import Sequence

from .models import MatchedRegion
from .tokenizer import Token

DEFAULT_SHINGLE_K = 5
MIN_MATCH_TOKENS = 3
MAX_MATCHED_BLOCKS = 5


def _effective_k(len_a: int, len_b: int, k: int) -> int:
    if k < 1:
        raise ValueError("Shingle size k must be >= 1.")
    shortest = min(len_a, len_b)
    if shortest == 0:
        return 0
    return min(k, shortest)


def shingles(tokens: Sequence[str], k: int) -> set[tuple[str, ...]]:
    """Return the set of contiguous ``k``-token shingles."""
    if k < 1:
        raise ValueError("Shingle size k must be >= 1.")
    if len(tokens) < k:
        return set()
    return {tuple(tokens[i : i + k]) for i in range(len(tokens) - k + 1)}


def jaccard_similarity(a: Sequence[str], b: Sequence[str], k: int = DEFAULT_SHINGLE_K) -> float:
    """Jaccard similarity over token shingles, in ``[0, 1]``.

    - Both empty (no tokens): ``1.0`` (vacuously identical).
    - One empty: ``0.0``.
    - Shorter than ``k``: backs off to ``k = min(len(a), len(b))`` so
      short programs still produce a defined score.
    """
    keff = _effective_k(len(a), len(b), k)
    if keff == 0:
        return 1.0 if len(a) == 0 and len(b) == 0 else 0.0
    sa = shingles(a, keff)
    sb = shingles(b, keff)
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    inter = len(sa & sb)
    union = len(sa | sb)
    return inter / union if union else 1.0


def sequence_similarity(a: Sequence[str], b: Sequence[str]) -> float:
    """Token-order similarity via :class:`difflib.SequenceMatcher`.

    Returns ``1.0`` for two empty sequences, ``0.0`` when exactly one is
    empty, otherwise ``SequenceMatcher.ratio()`` in ``[0, 1]``.
    """
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, list(a), list(b)).ratio()


def combined_similarity(token_sim: float, structural_sim: float) -> float:
    """Documented combination: unweighted mean of the two components."""
    return (token_sim + structural_sim) / 2.0


def to_percentage(score: float) -> float:
    """Convert a ``[0, 1]`` score to a ``[0, 100]`` percentage."""
    return round(max(0.0, min(1.0, score)) * 100.0, 2)


def find_matched_regions(
    tokens_a: list[Token],
    source_a: str,
    tokens_b: list[Token],
    source_b: str,
    min_match: int = MIN_MATCH_TOKENS,
    max_blocks: int = MAX_MATCHED_BLOCKS,
) -> list[MatchedRegion]:
    """Find traceable overlapping token regions between two submissions.

    Uses ``SequenceMatcher.get_matching_blocks()`` on token *texts*, keeps
    blocks with length >= ``min_match``, and maps token indices back to
    character offsets so every snippet satisfies
    ``source[char_start:char_end] == snippet``.
    """
    texts_a = [t.text for t in tokens_a]
    texts_b = [t.text for t in tokens_b]
    if not texts_a or not texts_b:
        return []
    matcher = difflib.SequenceMatcher(None, texts_a, texts_b, autojunk=False)
    blocks = [b for b in matcher.get_matching_blocks() if b.size >= min_match]
    # Deterministic order: largest first, then by position.
    blocks.sort(key=lambda b: (-b.size, b.a, b.b))
    regions: list[MatchedRegion] = []
    for block in blocks[:max_blocks]:
        ta0, tb0, size = block.a, block.b, block.size
        ta1, tb1 = ta0 + size, tb0 + size
        ca0 = tokens_a[ta0].start
        ca1 = tokens_a[ta1 - 1].end
        cb0 = tokens_b[tb0].start
        cb1 = tokens_b[tb1 - 1].end
        snippet_a = source_a[ca0:ca1]
        snippet_b = source_b[cb0:cb1]
        regions.append(
            MatchedRegion(
                token_start_a=ta0,
                token_end_a=ta1,
                token_start_b=tb0,
                token_end_b=tb1,
                char_start_a=ca0,
                char_end_a=ca1,
                char_start_b=cb0,
                char_end_b=cb1,
                token_length=size,
                snippet_a=snippet_a,
                snippet_b=snippet_b,
            )
        )
    return regions


#: Boilerplate token patterns per language. A pattern is reported when it
#: appears contiguously in *both* submissions; it inflates similarity but
#: is weak plagiarism evidence on its own.
BOILERPLATE_PATTERNS: dict[str, list[tuple[str, ...]]] = {
    "python": [
        ("import", "os"),
        ("import", "sys"),
        ("import", "typing"),
        ("from", "typing", "import"),
        ("if", "__name__", "==", "__main__"),
        ("def", "main", "(", ")"),
    ],
    "java": [
        ("package",),
        ("import", "java"),
        ("public", "class"),
        ("public", "static", "void", "main"),
        ("System", ".", "out", ".", "println"),
        ("@Override",),
    ],
}


def boilerplate_overlap(
    texts_a: Sequence[str], texts_b: Sequence[str], language: str
) -> list[str]:
    """Return boilerplate pattern labels present in both token streams."""
    joined_a = "\x00".join(texts_a)
    joined_b = "\x00".join(texts_b)
    matched: list[str] = []
    for pattern in BOILERPLATE_PATTERNS.get(language, []):
        needle = "\x00".join(pattern)
        if needle and needle in joined_a and needle in joined_b:
            matched.append(" ".join(pattern))
    return matched
