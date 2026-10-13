"""CodeProof AI detector — Phase 1 baseline (stdlib only, no execution)."""

from .comparison import compare_all, compare_pair
from .models import (
    MAX_SOURCE_CHARS,
    MAX_SUBMISSIONS,
    SUPPORTED_LANGUAGES,
    MatchedRegion,
    PairComparison,
    Submission,
    SubmissionResult,
)
from .reporting import analyze_submissions, summarize_best_matches
from .similarity import (
    combined_similarity,
    find_matched_regions,
    jaccard_similarity,
    sequence_similarity,
    shingles,
    to_percentage,
)
from .tokenizer import Token, TokenizeResult, tokenize
from .validation import ValidationError, normalize_language, validate_submissions

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "analyze_submissions",
    "summarize_best_matches",
    "compare_all",
    "compare_pair",
    "validate_submissions",
    "normalize_language",
    "ValidationError",
    "tokenize",
    "Token",
    "TokenizeResult",
    "Submission",
    "SubmissionResult",
    "PairComparison",
    "MatchedRegion",
    "SUPPORTED_LANGUAGES",
    "MAX_SOURCE_CHARS",
    "MAX_SUBMISSIONS",
    "shingles",
    "jaccard_similarity",
    "sequence_similarity",
    "combined_similarity",
    "find_matched_regions",
    "to_percentage",
]
