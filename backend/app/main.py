"""CodeProof API: FastAPI wrapper for the Phase 1 AI detector."""

import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DETECTOR_SOURCE = PROJECT_ROOT / "ai-detector" / "src"

if not DETECTOR_SOURCE.is_dir():
    raise RuntimeError(
        f"Detector source directory not found: {DETECTOR_SOURCE}"
    )

sys.path.insert(0, str(DETECTOR_SOURCE))

from codeproof_detector import analyze_submissions
from codeproof_detector import ValidationError as DetectorValidationError

app = FastAPI(
    title="CodeProof API",
    description=(
        "API for comparing Python and Java source submissions. "
        "Similarity scores are indicators, not proof of plagiarism."
    ),
    version="0.1.0",
)


class AnalyzeRequest(BaseModel):
    """Request body for a batch similarity analysis."""

    model_config = ConfigDict(extra="forbid")

    submissions: list[dict[str, Any]] = Field(min_length=1, max_length=100)
    shingle_k: int = Field(default=5, ge=1)


@app.get("/health")
def health() -> dict[str, str]:
    """Report whether the API process is running."""
    return {"status": "ok", "service": "codeproof-api"}


@app.post("/api/v1/analyze")
def analyze(request: AnalyzeRequest) -> dict[str, Any]:
    """Analyze submissions and return the detector report."""
    try:
        return analyze_submissions(
            request.submissions,
            shingle_k=request.shingle_k,
        )
    except (DetectorValidationError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

from app.auth import router as auth_router
app.include_router(auth_router)
