\# CodeProof AI Detector — Evaluation Report



\## 1. Objective



This report evaluates the Phase 1 CodeProof code-similarity detector using five synthetic Python code-pair scenarios. The objective is to observe how token similarity, structural similarity, and combined similarity behave under different types of code overlap.



These experiments are preliminary and do not establish the detector's accuracy on real-world student submissions.



\## 2. Evaluation Method



The detector uses two similarity measures:



\- \*\*Token similarity:\*\* Jaccard similarity calculated over token shingles.

\- \*\*Structural similarity:\*\* Sequence similarity calculated over token sequences.

\- \*\*Combined similarity:\*\* Arithmetic mean of token similarity and structural similarity.



The combined score is calculated as:



`Combined similarity = (Token similarity + Structural similarity) / 2`



The detector also reports matched code regions and warnings where applicable. Submitted code is treated as text and is not executed.



\## 3. Test Environment



\- Project: CodeProof

\- Module: AI Detector, Phase 1 baseline

\- Languages supported by the baseline: Python and Java

\- Evaluation language: Python

\- Test dataset: Five synthetic code-pair scenarios

\- Existing automated test suite: 33 tests passed during this evaluation



\## 4. Results



| Scenario | Token Similarity | Structural Similarity | Combined Similarity |

|---|---:|---:|---:|

| Identical code | 100.00% | 100.00% | 100.00% |

| Formatting/comment changes | 100.00% | 100.00% | 100.00% |

| Renamed identifiers | 0.00% | 57.89% | 28.95% |

| Different implementation | 0.00% | 33.33% | 16.67% |

| Shared copied fragment | 47.06% | 89.66% | 68.36% |



\## 5. Observations



\### 5.1 Identical Code



The identical code pair received 100% for all three measures. One matched region was reported, as expected for identical token sequences.



\### 5.2 Formatting and Comment Changes



The pair received 100% similarity across all measures. This demonstrates that the tokenizer ignores the tested whitespace and comment differences.



\### 5.3 Renamed Identifiers



The token similarity was 0%, while structural similarity was 57.89%. The result illustrates a limitation of the baseline: changing identifiers can reduce token-shingle overlap even when the overall logic remains similar.



\### 5.4 Different Implementation



The pair received a combined similarity score of 16.67%. This was lower than the shared-fragment scenario in this evaluation. The result applies only to the particular examples tested and does not establish a universal threshold for unrelated code.



\### 5.5 Shared Copied Fragment



The pair received 47.06% token similarity and 89.66% structural similarity, resulting in 68.36% combined similarity. This illustrates how shared sequences can influence similarity measures even when function and variable names differ.



\## 6. Limitations



\- Only five synthetic code-pair scenarios were evaluated.

\- No labeled real-world dataset was used.

\- The results do not establish precision, recall, false-positive rate, or false-negative rate.

\- Short programs can produce unreliable or inflated similarity scores.

\- Renamed identifiers and reordered logic can affect the scores.

\- Similar code can result from common programming patterns or assignment requirements.

\- Embedding similarity is not implemented in Phase 1.

\- Similarity scores are not proof of plagiarism or authorship.



\## 7. Future Improvements



Potential future work includes:



1\. Expanding the evaluation dataset with additional controlled code pairs.

2\. Evaluating identifier normalization to better handle renamed variables.

3\. Testing partial copying and reordered statements.

4\. Measuring precision and recall using an appropriately labeled dataset.

5\. Benchmarking execution time on larger submissions.



Changes to the algorithm should be considered only after additional testing.



\## 8. Conclusion



The preliminary evaluation demonstrates that the CodeProof Phase 1 detector can identify identical token sequences, tolerate the tested formatting and comment changes, and report varying similarity scores for renamed identifiers, different implementations, and shared code fragments.



The findings are limited to the synthetic examples tested. The detector should be used to support manual review rather than make automatic plagiarism determinations.



\## 9. Reproducibility



Run the evaluation from the repository root:



`python .\\ai-detector\\examples\\evaluate\_similarity.py`



Run the existing detector tests:



`python -m pytest .\\ai-detector\\tests -q`
