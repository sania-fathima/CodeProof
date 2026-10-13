"""Structured, JSON-serializable reporting and the stable entry point."""

from __future__ import annotations

from typing import Any

from .comparison import compare_all
from .models import Submission
from .similarity import to_percentage
from .validation import validate_submissions

METHOD_DESCRIPTION = (
    "Phase 1 baseline: language-aware tokenization (whitespace/comments "
    "ignored), token-shingle Jaccard similarity plus token-sequence "
    "similarity (difflib ratio); combined = mean of the two. "
    "No ML embeddings, no external APIs."
)

DISCLAIMER = (
    "Similarity scores are algorithmic indicators of textual overlap and "
    "do NOT constitute proof of plagiarism. High scores require manual "
    "review; boilerplate and short programs inflate or destabilize scores."
)


def analyze_submissions(raw_submissions: Any, shingle_k: int = 5) -> dict[str, Any]:
    """Validate, compare, and report on a batch of submissions.

    This is the stable callable the backend team imports::

        from codeproof_detector import analyze_submissions
        report = analyze_submissions([
            {"submission_id": "a", "language": "python",
             "source_code": "def f():\\n    return 1\\n"},
            {"submission_id": "b", "language": "python",
             "source_code": "def f():\\n    return 1\\n"},
        ])

    Args:
        raw_submissions: List of ``{"submission_id", "language",
            "source_code"}`` dicts (or :class:`Submission` objects).
        shingle_k: Token-shingle size for Jaccard similarity.

    Returns:
        JSON-serializable ``dict`` with keys ``results`` (per-submission
        comparisons), ``method``, ``warnings`` and ``disclaimer``.

    Raises:
        ValidationError: If input fails validation.
        ValueError: If ``shingle_k < 1``.
    """
    if not isinstance(shingle_k, int) or shingle_k < 1:
        raise ValueError("shingle_k must be an integer >= 1.")
    submissions: list[Submission] = validate_submissions(raw_submissions)
    results = compare_all(submissions, shingle_k=shingle_k)

    top_warnings: list[str] = []
    languages = sorted({s.language for s in submissions})
    if len(languages) > 1:
        top_warnings.append(
            "Multiple languages submitted; only same-language pairs compared."
        )

    return {
        "results": [r.to_dict() for r in results],
        "method": METHOD_DESCRIPTION,
        "warnings": top_warnings,
        "disclaimer": DISCLAIMER,
        "score_to_percentage": "multiply a [0,1] score by 100 "
        "(helper: codeproof_detector.similarity.to_percentage).",
    }


def summarize_best_matches(report: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten a report to best-match rows (convenience for backends)."""
    rows: list[dict[str, Any]] = []
    for res in report.get("results", []):
        best = None
        for comp in res.get("comparisons", []):
            if best is None or comp["combined_similarity"] > best["combined_similarity"]:
                best = comp
        rows.append(
            {
                "submission_id": res["submission_id"],
                "language": res["language"],
                "num_comparisons": len(res.get("comparisons", [])),
                "best_match_id": best["compared_submission_id"] if best else None,
                "best_combined_similarity": best["combined_similarity"] if best else None,
                "best_similarity_percentage": (
                    to_percentage(best["combined_similarity"]) if best else None
                ),
            }
        )
    return rows
