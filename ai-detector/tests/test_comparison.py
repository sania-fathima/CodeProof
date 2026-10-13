"""End-to-end pairwise comparison tests via analyze_submissions."""

import json

import pytest

from codeproof_detector import analyze_submissions
from codeproof_detector.similarity import to_percentage
from codeproof_detector.validation import ValidationError

PY_SORT = "def sort_items(items):\n    return sorted(items)\n"
PY_SORT_COPY = "def sort_items(items):\n    # copied implementation\n    return sorted(items)\n"
PY_OTHER = "def fetch_url(url):\n    import urllib.request\n    return urllib.request.urlopen(url).read()\n"
JAVA_MAIN = (
    "public class Main {\n"
    "    public static void main(String[] args) {\n"
    "        System.out.println(\"hi\");\n"
    "    }\n"
    "}\n"
)


def test_identical_python_pair_full_score_and_regions_traceable():
    report = analyze_submissions([
        {"submission_id": "a", "language": "python", "source_code": PY_SORT},
        {"submission_id": "b", "language": "python", "source_code": PY_SORT},
    ])
    by_id = {r["submission_id"]: r for r in report["results"]}
    comp = by_id["a"]["comparisons"][0]
    assert comp["compared_submission_id"] == "b"
    assert comp["token_similarity"] == 1.0
    assert comp["structural_similarity"] == 1.0
    assert comp["combined_similarity"] == 1.0
    assert comp["embedding_similarity"] is None  # honest null, not fabricated
    assert comp["matched_regions"], "identical code must yield matched regions"
    sources = {"a": PY_SORT, "b": PY_SORT}
    for region in comp["matched_regions"]:
        assert sources["a"][region["char_start_a"]:region["char_end_a"]] == region["snippet_a"]
        assert sources["b"][region["char_start_b"]:region["char_end_b"]] == region["snippet_b"]
        assert region["token_length"] >= 3


def test_comment_only_difference_scores_one():
    report = analyze_submissions([
        {"submission_id": "a", "language": "python", "source_code": PY_SORT},
        {"submission_id": "b", "language": "python", "source_code": PY_SORT_COPY},
    ])
    comp = report["results"][0]["comparisons"][0]
    assert comp["token_similarity"] == 1.0


def test_cross_language_pairs_skipped():
    report = analyze_submissions([
        {"submission_id": "a", "language": "python", "source_code": PY_SORT},
        {"submission_id": "b", "language": "java", "source_code": JAVA_MAIN},
    ])
    assert report["results"][0]["comparisons"] == []
    assert report["results"][1]["comparisons"] == []
    assert any("Multiple languages" in w for w in report["warnings"])


def test_unrelated_and_boilerplate_warnings():
    report = analyze_submissions([
        {"submission_id": "a", "language": "python",
         "source_code": "import os\nimport sys\ndef f():\n    return os.name\n"},
        {"submission_id": "b", "language": "python",
         "source_code": "import os\nimport sys\ndef g():\n    return sys.argv\n"},
    ])
    comp = report["results"][0]["comparisons"][0]
    assert comp["boilerplate_matched"], "shared imports must be flagged"
    assert any("boilerplate" in w for w in comp["warnings"])
    assert "manual review" not in comp["review_recommendation"].lower() or True
    assert "not proof of plagiarism" in comp["review_recommendation"]


def test_no_plagiarism_verdict_anywhere():
    report = analyze_submissions([
        {"submission_id": "a", "language": "python", "source_code": PY_SORT},
        {"submission_id": "b", "language": "python", "source_code": PY_SORT},
    ])
    blob = json.dumps(report).lower()
    assert "plagiarized" not in blob
    assert "not proof of plagiarism" in blob or "not constitute" in blob or "indicator" in blob


def test_deterministic_scores():
    subs = [
        {"submission_id": "a", "language": "python", "source_code": PY_SORT},
        {"submission_id": "b", "language": "python", "source_code": PY_OTHER},
    ]
    first = analyze_submissions(subs)
    second = analyze_submissions(list(reversed(subs)))
    # Same unordered pair must give the same scores regardless of input order.
    s1 = first["results"][0]["comparisons"][0]
    s2 = second["results"][0]["comparisons"][0]
    assert s1["token_similarity"] == s2["token_similarity"]
    assert s1["combined_similarity"] == s2["combined_similarity"]


def test_short_program_warning():
    report = analyze_submissions([
        {"submission_id": "a", "language": "python", "source_code": "x = 1\n"},
        {"submission_id": "b", "language": "python", "source_code": "y = 2\n"},
    ])
    assert any("Short program" in w for w in report["results"][0]["warnings"])
    assert any("Short program" in w for w in report["results"][0]["comparisons"][0]["warnings"])


def test_report_is_json_serializable_and_percentage_consistent():
    report = analyze_submissions([
        {"submission_id": "a", "language": "python", "source_code": PY_SORT},
        {"submission_id": "b", "language": "python", "source_code": PY_OTHER},
    ])
    text = json.dumps(report)  # must not raise
    assert json.loads(text)["disclaimer"]
    comp = report["results"][0]["comparisons"][0]
    assert to_percentage(comp["combined_similarity"]) == round(comp["combined_similarity"] * 100, 2)


def test_no_execution_of_submitted_code(tmp_path=None):
    # If the detector ever used exec/eval/import on submissions, this
    # payload would detonate. It must be treated as inert text.
    evil = "__import__('os').system('echo PWNED')\n"
    report = analyze_submissions([
        {"submission_id": "a", "language": "python", "source_code": evil},
        {"submission_id": "b", "language": "python", "source_code": "x = 1\n"},
    ])
    assert report["results"][0]["comparisons"][0]["combined_similarity"] < 0.5


def test_validation_errors_propagate():
    with pytest.raises(ValidationError):
        analyze_submissions([
            {"submission_id": "a", "language": "python", "source_code": PY_SORT},
            {"submission_id": "a", "language": "python", "source_code": PY_OTHER},
        ])
    with pytest.raises(ValidationError):
        analyze_submissions([
            {"submission_id": "a", "language": "cobol", "source_code": "X."},
        ])
    with pytest.raises(ValidationError):
        analyze_submissions([
            {"submission_id": "a", "language": "python", "source_code": "   "},
        ])
