"""Validation tests: missing fields, duplicates, sizes, languages."""

import pytest

from codeproof_detector.models import MAX_SOURCE_CHARS, Submission
from codeproof_detector.validation import ValidationError, validate_submissions


def _sub(sid="a", lang="python", code="def f():\n    return 1\n"):
    return {"submission_id": sid, "language": lang, "source_code": code}


def test_valid_python_and_java_normalizes_case():
    out = validate_submissions([
        _sub("a", "Python", "def f():\n    return 1\n"),
        _sub("b", " JAVA ", "class A { int x; }\n"),
    ])
    assert [s.language for s in out] == ["python", "java"]


def test_missing_field_rejected():
    with pytest.raises(ValidationError):
        validate_submissions([{"submission_id": "a", "language": "python"}])


def test_non_list_and_empty_list_rejected():
    with pytest.raises(ValidationError):
        validate_submissions({"submission_id": "a"})
    with pytest.raises(ValidationError):
        validate_submissions([])


def test_duplicate_ids_rejected():
    with pytest.raises(ValidationError) as exc:
        validate_submissions([_sub("dup"), _sub("dup")])
    assert "Duplicate" in str(exc.value)


def test_empty_and_whitespace_source_rejected():
    with pytest.raises(ValidationError):
        validate_submissions([_sub("a", code="")])
    with pytest.raises(ValidationError):
        validate_submissions([_sub("a", code="   \n\t  ")])


def test_oversized_source_rejected():
    with pytest.raises(ValidationError):
        validate_submissions([_sub("a", code="x = 1\n" * ((MAX_SOURCE_CHARS // 6) + 10))])


def test_unsupported_language_rejected():
    with pytest.raises(ValidationError):
        validate_submissions([_sub("a", lang="solidity")])


def test_malformed_item_types_rejected():
    with pytest.raises(ValidationError):
        validate_submissions(["not-a-dict"])
    with pytest.raises(ValidationError):
        validate_submissions([_sub("a", code=123)])
    with pytest.raises(ValidationError):
        validate_submissions([_sub("a", lang=None)])


def test_null_bytes_rejected():
    with pytest.raises(ValidationError):
        validate_submissions([_sub("a", code="x = 1\n\x00\n")])


def test_submission_objects_accepted():
    out = validate_submissions([Submission("a", "python", "x = 1\n")])
    assert out[0].submission_id == "a"
