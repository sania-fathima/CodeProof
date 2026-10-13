"""Input validation for the CodeProof AI detector.

Never executes uploaded code. All checks are syntactic (types, sizes,
uniqueness) and raise :class:`ValidationError` with a clear message.
Frontend validation must never be trusted; this module re-validates
everything at the backend boundary.
"""

from __future__ import annotations

from typing import Any

from .models import (
    MAX_SOURCE_CHARS,
    MAX_SUBMISSIONS,
    SUPPORTED_LANGUAGES,
    Submission,
)


class ValidationError(ValueError):
    """Raised when detector input is missing, malformed, or unsafe."""


def _require_str(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise ValidationError(f"Field '{field}' must be a string.")
    return value


def normalize_language(language: Any) -> str:
    """Normalize and validate a language tag.

    Accepts case-insensitive ``"python"`` / ``"java"`` (with surrounding
    whitespace tolerated). Anything else raises :class:`ValidationError`.
    """
    if not isinstance(language, str):
        raise ValidationError("Field 'language' must be a string.")
    normalized = language.strip().lower()
    if normalized not in SUPPORTED_LANGUAGES:
        raise ValidationError(
            f"Unsupported language '{language}'. "
            f"Supported languages: {sorted(SUPPORTED_LANGUAGES)}."
        )
    return normalized


def validate_submissions(raw: Any) -> list[Submission]:
    """Validate a raw submission list into :class:`Submission` objects.

    Args:
        raw: Expected to be a list of ``dict`` objects (or already
            validated :class:`Submission` objects) with keys
            ``submission_id``, ``language`` and ``source_code``.

    Returns:
        Validated submissions in input order.

    Raises:
        ValidationError: On missing fields, duplicate IDs, empty or
            oversized source, unsupported languages, or malformed inputs.
    """
    if not isinstance(raw, list):
        raise ValidationError("Submissions must be provided as a list.")
    if len(raw) == 0:
        raise ValidationError("Submissions list must not be empty.")
    if len(raw) > MAX_SUBMISSIONS:
        raise ValidationError(
            f"Too many submissions ({len(raw)}). Maximum is {MAX_SUBMISSIONS}."
        )

    seen_ids: set[str] = set()
    validated: list[Submission] = []

    for index, item in enumerate(raw):
        where = f"submissions[{index}]"
        if isinstance(item, Submission):
            candidate = {
                "submission_id": item.submission_id,
                "language": item.language,
                "source_code": item.source_code,
            }
        elif isinstance(item, dict):
            candidate = item
        else:
            raise ValidationError(
                f"{where} must be an object with "
                "'submission_id', 'language' and 'source_code'."
            )

        if not isinstance(candidate, dict):
            raise ValidationError(f"{where} must be an object.")
        for key in ("submission_id", "language", "source_code"):
            if key not in candidate:
                raise ValidationError(f"{where} is missing field '{key}'.")

        sid = _require_str(candidate["submission_id"], "submission_id")
        if sid.strip() == "":
            raise ValidationError(f"{where}.submission_id must not be empty.")
        if sid in seen_ids:
            raise ValidationError(f"Duplicate submission_id '{sid}'.")
        seen_ids.add(sid)

        language = normalize_language(candidate["language"])

        source = candidate["source_code"]
        if not isinstance(source, str):
            raise ValidationError(f"{where}.source_code must be a string.")
        if source.strip() == "":
            raise ValidationError(
                f"{where}.source_code must not be empty or whitespace-only."
            )
        if len(source) > MAX_SOURCE_CHARS:
            raise ValidationError(
                f"{where}.source_code exceeds {MAX_SOURCE_CHARS} characters "
                f"(got {len(source)})."
            )
        if "\x00" in source:
            raise ValidationError(
                f"{where}.source_code contains null bytes; "
                "binary content is not accepted."
            )

        validated.append(
            Submission(submission_id=sid, language=language, source_code=source)
        )

    return validated
