"""Shared data models for the CodeProof AI detector (Phase 1 baseline).

All models are JSON-serializable via ``to_dict()`` so the FastAPI backend
team can consume results without importing web or database code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

#: Languages supported by the Phase 1 baseline.
SUPPORTED_LANGUAGES = frozenset({"python", "java"})

#: Maximum accepted source size per submission (chars). Aligned with the
#: per-file limit documented in ``docs/API_CONTRACT.md`` section 3.5.
MAX_SOURCE_CHARS = 500_000

#: Upper bound on submissions per call to keep O(n^2) pairwise
#: comparison tractable.
MAX_SUBMISSIONS = 100


@dataclass(frozen=True)
class Submission:
    """A single validated source-code submission."""

    submission_id: str
    language: str
    source_code: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "submission_id": self.submission_id,
            "language": self.language,
            "source_code": self.source_code,
        }


@dataclass(frozen=True)
class MatchedRegion:
    """A traceable overlap between two submissions.

    Character offsets index into the original ``source_code`` strings so
    every reported snippet can be verified with ``source[start:end]``.
    """

    token_start_a: int
    token_end_a: int
    token_start_b: int
    token_end_b: int
    char_start_a: int
    char_end_a: int
    char_start_b: int
    char_end_b: int
    token_length: int
    snippet_a: str
    snippet_b: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "token_start_a": self.token_start_a,
            "token_end_a": self.token_end_a,
            "token_start_b": self.token_start_b,
            "token_end_b": self.token_end_b,
            "char_start_a": self.char_start_a,
            "char_end_a": self.char_end_a,
            "char_start_b": self.char_start_b,
            "char_end_b": self.char_end_b,
            "token_length": self.token_length,
            "snippet_a": self.snippet_a,
            "snippet_b": self.snippet_b,
        }


@dataclass(frozen=True)
class PairComparison:
    """Pairwise comparison of one submission against another."""

    compared_submission_id: str
    token_similarity: float
    structural_similarity: Optional[float]
    embedding_similarity: Optional[float] = None
    combined_similarity: Optional[float] = None
    matched_regions: list[MatchedRegion] = field(default_factory=list)
    boilerplate_matched: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    review_recommendation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "compared_submission_id": self.compared_submission_id,
            "token_similarity": self.token_similarity,
            "structural_similarity": self.structural_similarity,
            "embedding_similarity": self.embedding_similarity,
            "combined_similarity": self.combined_similarity,
            "matched_regions": [r.to_dict() for r in self.matched_regions],
            "boilerplate_matched": list(self.boilerplate_matched),
            "warnings": list(self.warnings),
            "review_recommendation": self.review_recommendation,
        }


@dataclass(frozen=True)
class SubmissionResult:
    """All pairwise comparisons for a single submission."""

    submission_id: str
    language: str
    num_tokens: int
    comparisons: list[PairComparison] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "submission_id": self.submission_id,
            "language": self.language,
            "num_tokens": self.num_tokens,
            "comparisons": [c.to_dict() for c in self.comparisons],
            "warnings": list(self.warnings),
        }
