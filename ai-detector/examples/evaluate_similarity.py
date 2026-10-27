
"""Evaluate CodeProof similarity scores on synthetic code examples.

Run from the repository root:
        python ai-detector/examples/evaluate_similarity.py

Scores are indicators of code similarity, not proof of plagiarism.
"""

import os
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "src")
)

from codeproof_detector import analyze_submissions


CASES = [
    (
        "Identical code",
        "def calculate_total(values):\n"
        "    total = 0\n"
        "    for value in values:\n"
        "        total += value\n"
        "    return total\n",
        "def calculate_total(values):\n"
        "    total = 0\n"
        "    for value in values:\n"
        "        total += value\n"
        "    return total\n",
    ),
    (
        "Formatting/comment changes",
        "def calculate_total(values):\n"
        "    total = 0\n"
        "    for value in values:\n"
        "        total += value\n"
        "    return total\n",
        "def calculate_total(values):  # calculate sum\n"
        "    total=0\n"
        "    for value in values:\n"
        "        total+=value\n"
        "    return total\n",
    ),
    (
        "Renamed identifiers",
        "def calculate_total(values):\n"
        "    total = 0\n"
        "    for value in values:\n"
        "        total += value\n"
        "    return total\n",
        "def sum_numbers(numbers):\n"
        "    result = 0\n"
        "    for number in numbers:\n"
        "        result += number\n"
        "    return result\n",
    ),
    (
        "Different implementation",
        "def calculate_total(values):\n"
        "    total = 0\n"
        "    for value in values:\n"
        "        total += value\n"
        "    return total\n",
        "def find_maximum(numbers):\n"
        "    if not numbers:\n"
        "        return None\n"
        "    return max(numbers)\n",
    ),
    (
        "Shared copied fragment",
        "def process_order(items):\n"
        "    subtotal = 0\n"
        "    for item in items:\n"
        "        subtotal += item['price']\n"
        "    tax = subtotal * 0.1\n"
        "    return subtotal + tax\n",
        "def calculate_invoice(products):\n"
        "    subtotal = 0\n"
        "    for item in products:\n"
        "        subtotal += item['price']\n"
        "    tax = subtotal * 0.1\n"
        "    return subtotal + tax\n",
    ),
]


def main():
    print("CodeProof AI Detector - Similarity Evaluation")
    print("=" * 78)

    for index, (label, source_a, source_b) in enumerate(CASES, start=1):
        report = analyze_submissions([
            {
                "submission_id": "submission_a",
                "language": "python",
                "source_code": source_a,
            },
            {
                "submission_id": "submission_b",
                "language": "python",
                "source_code": source_b,
            },
        ])

        result_a = next(
            item for item in report["results"]
            if item["submission_id"] == "submission_a"
        )
        comparison = next(
            item for item in result_a["comparisons"]
            if item["compared_submission_id"] == "submission_b"
        )

        print(f"\n{index}. {label}")
        print(f"   Token similarity:      "
              f"{comparison['token_similarity'] * 100:.2f}%")
        print(f"   Structural similarity: "
              f"{comparison['structural_similarity'] * 100:.2f}%")
        print(f"   Combined similarity:   "
              f"{comparison['combined_similarity'] * 100:.2f}%")
        print(f"   Matched regions:       "
              f"{len(comparison['matched_regions'])}")
        if comparison["warnings"]:
            print(f"   Warnings:              "
                  f"{'; '.join(comparison['warnings'])}")

    print("\n" + "=" * 78)
    print("Scores indicate similarity; they do not establish plagiarism.")


if __name__ == "__main__":
    main()
