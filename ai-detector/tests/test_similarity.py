"""Similarity + tokenizer behavior tests (no mocked scores)."""

import pytest

from codeproof_detector.similarity import (
    boilerplate_overlap,
    jaccard_similarity,
    sequence_similarity,
    shingles,
    to_percentage,
)
from codeproof_detector.tokenizer import tokenize

PY_A = "def add(a, b):\n    # sum two numbers\n    return a + b\n"
PY_A_WS = "def   add(a,b):\n\n    # different comment\n    return a+b\n"
PY_RENAMED = "def add(x, y):\n    return x + y\n"
PY_OTHER = "def greet(name):\n    print('hello ' + name)\n"

JAVA_A = (
    "public class Add {\n"
    "    // sums two numbers\n"
    "    public int add(int a, int b) { return a + b; }\n"
    "}\n"
)
JAVA_A_WS = "public class Add{public int add(int a,int b){return a+b;}}\n"


def test_identical_python_scores_one():
    a = tokenize(PY_A, "python").texts()
    b = tokenize(PY_A, "python").texts()
    assert jaccard_similarity(a, b) == 1.0
    assert sequence_similarity(a, b) == 1.0


def test_identical_java_scores_one():
    a = tokenize(JAVA_A, "java").texts()
    assert jaccard_similarity(a, list(a)) == 1.0
    assert sequence_similarity(a, list(a)) == 1.0


def test_whitespace_and_comments_ignored():
    a = tokenize(PY_A, "python").texts()
    b = tokenize(PY_A_WS, "python").texts()
    assert a == b  # comments/whitespace produce identical token streams
    assert jaccard_similarity(a, b) == 1.0
    ja = tokenize(JAVA_A, "java").texts()
    jb = tokenize(JAVA_A_WS, "java").texts()
    assert ja == jb


def test_renamed_identifiers_still_high_sequence_but_lower_jaccard():
    a = tokenize(PY_A, "python").texts()
    r = tokenize(PY_RENAMED, "python").texts()
    assert a != r  # raw tokens differ (no identifier normalization in baseline)
    seq = sequence_similarity(a, r)
    jac = jaccard_similarity(a, r)
    assert seq > 0.5  # structure preserved
    assert jac < 1.0


def test_unrelated_programs_low_scores():
    a = tokenize(PY_A, "python").texts()
    b = tokenize(PY_OTHER, "python").texts()
    assert jaccard_similarity(a, b) < 0.3
    assert sequence_similarity(a, b) < 0.6


def test_boilerplate_detected():
    a = tokenize("import os\nimport sys\nx = 1\n", "python").texts()
    b = tokenize("import os\nimport sys\ny = 2\n", "python").texts()
    matched = boilerplate_overlap(a, b, "python")
    assert any("import os" in m for m in matched)


def test_short_programs_defined_and_deterministic():
    a = tokenize("x = 1\n", "python").texts()
    b = tokenize("x = 1\n", "python").texts()
    assert jaccard_similarity(a, b) == 1.0
    c = tokenize("y = 2\n", "python").texts()
    first = (jaccard_similarity(a, c), sequence_similarity(a, c))
    second = (jaccard_similarity(a, c), sequence_similarity(a, c))
    assert first == second


def test_empty_token_edge_cases():
    assert jaccard_similarity([], []) == 1.0
    assert jaccard_similarity(["a"], []) == 0.0
    assert sequence_similarity([], []) == 1.0


def test_strings_with_comment_markers_not_stripped():
    src = 'x = "# not a comment"\ny = "// also not a comment"\n'
    texts = tokenize(src, "python").texts()
    joined = " ".join(texts)
    assert "# not a comment" in joined
    assert "// also not a comment" in joined
    jsrc = 'String s = "// not a comment"; // real comment\nint x = 1;\n'
    jtexts = tokenize(jsrc, "java").texts()
    assert any("// not a comment" in t for t in jtexts)
    assert not any(t == "// real comment" for t in jtexts)


def test_malformed_source_does_not_raise_and_uses_fallback_or_partial():
    bad = "def broken(:\n    this is (not python!!!\n"
    res = tokenize(bad, "python")
    assert isinstance(res.texts(), list)  # never crashes
    bad_java = "public class A { String s = \"unterminated; \n"
    res_j = tokenize(bad_java, "java")
    assert isinstance(res_j.texts(), list)
    assert any("Unterminated" in w for w in res_j.warnings)


def test_unsupported_language_raises():
    with pytest.raises(ValueError):
        tokenize("x", "solidity")


def test_percentage_conversion_documented():
    assert to_percentage(0.784) == 78.4
    assert to_percentage(1.0) == 100.0
    assert to_percentage(0.0) == 0.0


def test_shingles_validation():
    with pytest.raises(ValueError):
        shingles(["a"], 0)
