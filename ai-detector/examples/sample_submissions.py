"""Synthetic end-to-end example (no real student data).

Run from ``ai-detector/``::

    py -m pytest -q
    py examples/sample_submissions.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from codeproof_detector import analyze_submissions  # noqa: E402

SUBMISSIONS = [
    {
        "submission_id": "student_a",
        "language": "python",
        "source_code": (
            "def total(xs):\n"
            "    # sum a list\n"
            "    s = 0\n"
            "    for x in xs:\n"
            "        s += x\n"
            "    return s\n"
        ),
    },
    {
        "submission_id": "student_b",
        "language": "python",
        "source_code": (
            "def total(xs):\n"
            "    s=0\n"
            "    for x in xs:\n"
            "        s+=x\n"
            "    return s\n"
        ),
    },
    {
        "submission_id": "student_c",
        "language": "python",
        "source_code": (
            "def fetch_url(url):\n"
            "    import urllib.request\n"
            "    return urllib.request.urlopen(url).read()\n"
        ),
    },
]


def main() -> None:
    report = analyze_submissions(SUBMISSIONS)
    print(json.dumps(report, indent=2)[:2000])


if __name__ == "__main__":
    main()
