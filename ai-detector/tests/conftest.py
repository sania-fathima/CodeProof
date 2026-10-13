"""Pytest bootstrap: make ``codeproof_detector`` importable without install."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
