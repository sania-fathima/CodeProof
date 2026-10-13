# CodeProof AI Detector — Phase 1 Baseline

Deterministic, dependency-free (stdlib-only) code-similarity baseline for
**Python** and **Java**. It never executes uploaded code.

> Similarity scores are algorithmic indicators of textual overlap and do
> **NOT** constitute proof of plagiarism.

## Layout

```text
ai-detector/
├── README.md
├── requirements.txt        # dev/test only (pytest); runtime is stdlib-only
├── pytest.ini
├── src/codeproof_detector/
│   ├── __init__.py         # public re-exports, __version__
│   ├── models.py           # Submission / PairComparison / SubmissionResult
│   ├── validation.py       # strict input validation (ValidationError)
│   ├── tokenizer.py        # Python (stdlib tokenize) + Java (custom lexer)
│   ├── similarity.py       # shingle Jaccard + SequenceMatcher + regions
│   ├── comparison.py       # same-language pairwise comparison
│   └── reporting.py        # analyze_submissions() + JSON report
├── tests/
│   ├── test_validation.py
│   ├── test_similarity.py
│   └── test_comparison.py
└── examples/sample_submissions.py
```

## Install / test

```bash
cd ai-detector
py -m pip install -r requirements.txt
py -m pytest -q
py examples/sample_submissions.py
```

Or without installing (conftest adds `src/` to `sys.path` automatically).

## Backend-friendly interface

```python
from codeproof_detector import analyze_submissions

report = analyze_submissions([
    {"submission_id": "a", "language": "python",
     "source_code": "def f():\n    return 1\n"},
    {"submission_id": "b", "language": "python",
     "source_code": "def f():\n    return 1\n"},
])
# report is JSON-serializable: {"results": [...], "method": ...,
#   "warnings": [...], "disclaimer": ...}
```

**Input** (`list[dict | Submission]`, max 100 items):
- `submission_id: str` — non-empty, unique.
- `language: str` — case-insensitive `"python"` or `"java"`.
- `source_code: str` — 1–500,000 chars, no null bytes.

Violations raise `ValidationError` (a `ValueError`). Source is never
executed.

**Output** per submission (`SubmissionResult.to_dict()`):
- `comparisons[]` against every *other same-language* submission, sorted
  by ID for determinism:
  - `compared_submission_id`, `token_similarity` ∈ [0,1] (shingle Jaccard),
    `structural_similarity` ∈ [0,1] (token `SequenceMatcher` ratio),
    `embedding_similarity: null` (not implemented in Phase 1),
    `combined_similarity = (token + structural) / 2`,
    `matched_regions[]` with char offsets/snippets verifiable via
    `source[start:end]`, `boilerplate_matched[]`, `warnings[]`,
    `review_recommendation` (operational guidance, never a verdict).
- Scores → percentages: `pct = round(score * 100, 2)`
  (`similarity.to_percentage()`).

## Method and limitations

- Tokenization ignores whitespace/comments; preserves keywords,
  identifiers, literals, operators. Malformed source uses a safe fallback
  (reported in warnings) instead of failing.
- Identical programs → 1.0; unrelated → low; short programs (< 20 tokens)
  and boilerplate (`import os`, `public static void main`, …) are flagged
  because scores are unreliable/inflated there.
- Token similarity misses renamed-identifier paraphrases partially
  (sequence score stays higher), reordered logic, and semantics. No
  threshold labels anything "plagiarized".

## API-contract notes (for backend teammate)

- `docs/API_CONTRACT.md` §5 describes a *proposal* (`solidity/js/ts`,
  TF-IDF, `analysis_id/files/corpus_reference_ids`). Phase 1 implements
  the detector-side baseline for `python`/`java` with a
  `[{submission_id, language, source_code}] → report` interface; the
  backend can map `files[].content → source_code` and
  `score → similarity_percentage` (×100). `structural_similarity` here is
  the sequence ratio; embeddings remain explicitly `null`.
- Open question: should Phase 2 add `java`↔contract mapping, or keep
  detector languages (`python`, `java`) separate from API languages?

## Future work (proposal only, not implemented)

- Identifier-normalized similarity / AST structure (benefit: catches
  renames; cost: parser deps + evaluation set needed).
- TF-IDF/embeddings (benefit: semantic recall; cost: model deps, GPU,
  calibration, bias review). Requires labeled pairs + threshold study
  before any verdict language.
