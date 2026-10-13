# CodeProof Backend

FastAPI service that exposes the CodeProof Phase 1 AI similarity detector through a REST API.

## Features

- Health-check endpoint
- Batch source-code similarity analysis
- Input validation and HTTP error handling
- Interactive API documentation through Swagger UI
- Integration with the existing Python/Java similarity detector

## Technology Stack

- Python
- FastAPI
- Uvicorn
- Pydantic
- Pytest

## Setup

Install dependencies from the repository root:

    .\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt

## Run the API

    .\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload

## Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Check API status |
| POST | `/api/v1/analyze` | Analyze submissions |
| GET | `/docs` | Interactive API documentation |

## Testing

    .\.venv\Scripts\python.exe -m pytest -q backend\tests
    py -m pytest -q ai-detector\tests

## Current Limitations

- Only Python and Java are supported by the Phase 1 detector.
- Submitted code is analyzed as text and is never executed.
- Similarity scores indicate overlap, not definitive proof of plagiarism.
- Authentication, database persistence, file uploads, and blockchain registration are not yet implemented in this backend service.
