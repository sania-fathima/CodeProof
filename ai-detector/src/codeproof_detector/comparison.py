"""Pairwise comparison over validated submissions.

Only submissions sharing the same language are compared. Scores come
directly from :mod:`codeproof_detector.similarity` applied to the actual
token streams — nothing is fabricated.
"""

from __future__ import annotations

from .models import PairComparison, Submission, SubmissionResult
from .similarity import (
    boilerplate_overlap,
    combined_similarity,
    find_matched_regions,
    jaccard_similarity,
    sequence_similarity,
)
from .tokenizer import Token, tokenize

#: Token counts below this trigger a short-program reliability warning.
SHORT_PROGRAM_TOKENS = 20


def review_recommendation(combined: float | None) -> str:
    """Operational review guidance (not a plagiarism verdict)."""
    base = "Similarity is an indicator of overlap, not proof of plagiarism."
    if combined is None:
        return "No combined score available. " + base
    if combined >= 0.8:
        return "High overlap — manual review recommended. " + base
    if combined >= 0.5:
        return "Moderate overlap — manual review suggested. " + base
    return "Low overlap — no action implied. " + base


def compare_pair(
    sub_a: Submission,
    tokens_a: list[Token],
    warnings_a: list[str],
    sub_b: Submission,
    tokens_b: list[Token],
    warnings_b: list[str],
    shingle_k: int = 5,
) -> PairComparison:
    """Compare two same-language submissions deterministically."""
    texts_a = [t.text for t in tokens_a]
    texts_b = [t.text for t in tokens_b]
    token_sim = jaccard_similarity(texts_a, texts_b, k=shingle_k)
    structural_sim = sequence_similarity(texts_a, texts_b)
    combined = combined_similarity(token_sim, structural_sim)
    regions = find_matched_regions(tokens_a, sub_a.source_code, tokens_b, sub_b.source_code)
    boilerplate = boilerplate_overlap(texts_a, texts_b, sub_a.language)

    warnings: list[str] = []
    if min(len(texts_a), len(texts_b)) < SHORT_PROGRAM_TOKENS:
        warnings.append(
            "Short program(s): similarity scores are less reliable "
            f"(< {SHORT_PROGRAM_TOKENS} tokens)."
        )
    if boilerplate:
        warnings.append(
            "Overlap includes common boilerplate "
            f"({'; '.join(boilerplate)}); treat score with caution."
        )
    for w in warnings_a + warnings_b:
        if w not in warnings:
            warnings.append(f"Tokenizer note: {w}")

    return PairComparison(
        compared_submission_id=sub_b.submission_id,
        token_similarity=token_sim,
        structural_similarity=structural_sim,
        embedding_similarity=None,  # Not implemented in Phase 1 baseline.
        combined_similarity=combined,
        matched_regions=regions,
        boilerplate_matched=boilerplate,
        warnings=warnings,
        review_recommendation=review_recommendation(combined),
    )


def compare_all(
    submissions: list[Submission], shingle_k: int = 5
) -> list[SubmissionResult]:
    """Compare every eligible same-language pair.

    Returns one :class:`SubmissionResult` per submission (in input order),
    each holding comparisons sorted by compared submission ID for
    determinism. Cross-language pairs are skipped (not comparable).
    """
    tokenized: dict[str, tuple[list[Token], list[str]]] = {}
    counts: dict[str, int] = {}
    for sub in submissions:
        result = tokenize(sub.source_code, sub.language)
        tokenized[sub.submission_id] = (result.tokens, result.warnings)
        counts[sub.submission_id] = len(result.tokens)

    by_id = {s.submission_id: s for s in submissions}
    results: list[SubmissionResult] = []
    for sub in submissions:
        tokens_a, warns_a = tokenized[sub.submission_id]
        comparisons: list[PairComparison] = []
        for other in sorted(submissions, key=lambda s: s.submission_id):
            if other.submission_id == sub.submission_id:
                continue
            if other.language != sub.language:
                continue
            tokens_b, warns_b = tokenized[other.submission_id]
            comparisons.append(
                compare_pair(sub, tokens_a, warns_a, other, tokens_b, warns_b, shingle_k)
            )
        sub_warnings: list[str] = []
        if counts[sub.submission_id] < SHORT_PROGRAM_TOKENS:
            sub_warnings.append(
                f"Short program: submission has {counts[sub.submission_id]} tokens "
                f"(< {SHORT_PROGRAM_TOKENS}); scores are less reliable."
            )
        if warns_a:
            sub_warnings.extend(f"Tokenizer note: {w}" for w in warns_a)
        _ = by_id  # (kept for readability of the pairwise loop)
        results.append(
            SubmissionResult(
                submission_id=sub.submission_id,
                language=sub.language,
                num_tokens=counts[sub.submission_id],
                comparisons=comparisons,
                warnings=sub_warnings,
            )
        )
    return results
