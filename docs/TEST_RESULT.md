# CodeProof — Test Results

## 1. Document Information

| Field | Details |
|---|---|
| Project | CodeProof |
| Document | Test Results |
| Version | 1.0 |
| Purpose | Record test execution outcomes and outstanding verification |
| Status | Partially verified; additional integration testing required |

## 2. Testing Summary

CodeProof contains separate frontend, backend, AI detector, and blockchain modules. Unit tests and API checks have been performed during development. The results below distinguish previously recorded test outcomes from tests that still require execution.

**Important:** Historical test counts are not a substitute for rerunning tests against the latest repository revision. Verify the current branch and commit before using these results in a final demonstration or academic report.

## 3. Previously Recorded Automated Test Results

| Module | Previously recorded result | Verification status |
|---|---|---|
| AI detector | 33 tests passed | Historical result; rerun against the current revision |
| Backend | 6 tests passed | Historical result; rerun against the current revision |
| Blockchain | 11 tests passed | Historical result; rerun against the current revision |

These results refer to earlier development test runs. They do not establish that every end-to-end workflow currently passes.

## 4. AI Detector Evaluation

A local evaluation script was created to compare five synthetic Python source-code pairs.

| Scenario | Token similarity | Structural similarity | Combined score |
|---|---:|---:|---:|
| Identical code | 100.00% | 100.00% | 100.00% |
| Formatting and comment changes | 100.00% | 100.00% | 100.00% |
| Renamed identifiers | 0.00% | 57.89% | 28.95% |
| Different implementation | 0.00% | 33.33% | 16.67% |
| Shared copied fragment | 47.06% | 89.66% | 68.36% |

These scores were obtained from the previously recorded evaluation run. They illustrate the behavior of the current heuristic approach on the selected examples, not its general accuracy on real-world student submissions.

Short programs may produce warnings because there are too few tokens for reliable comparison. Identifier renaming and implementation changes can also affect scores.

Supporting files:

- `ai-detector/examples/evaluate_similarity.py`
- `ai-detector/EVALUATION_REPORT.md`

## 5. Blockchain Verification

During local development, the registry contract was tested using a Hardhat development network. Previously recorded checks included successful registration and verification of a registered project fingerprint, as well as a negative verification check for an unregistered fingerprint.

The contract's automated test suite previously reported 11 passing tests.

For a new test session, record the following evidence:

| Test | Result for latest run | Evidence |
|---|---|---|
| Register a valid fingerprint | Pending rerun | Record transaction or
