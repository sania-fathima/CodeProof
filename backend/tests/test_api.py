from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def sample_submissions():
    return [
        {
            "submission_id": "a",
            "language": "python",
            "source_code": "def calculate():\n    return 42\n",
        },
        {
            "submission_id": "b",
            "language": "python",
            "source_code": "def calculate():\n    return 42\n",
        },
    ]


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_analyze_returns_detector_report():
    response = client.post(
        "/api/v1/analyze",
        json={"submissions": sample_submissions()},
    )

    assert response.status_code == 200
    report = response.json()
    assert "results" in report
    assert "method" in report
    assert "warnings" in report
    assert "disclaimer" in report
    assert len(report["results"]) == 2
    assert report["disclaimer"]


def test_empty_submissions_are_rejected():
    response = client.post(
        "/api/v1/analyze",
        json={"submissions": []},
    )

    assert response.status_code == 422


def test_unsupported_language_is_rejected():
    submissions = sample_submissions()
    submissions[0]["language"] = "javascript"

    response = client.post(
        "/api/v1/analyze",
        json={"submissions": submissions},
    )

    assert response.status_code == 422


def test_duplicate_submission_ids_are_rejected():
    submissions = sample_submissions()
    submissions[1]["submission_id"] = submissions[0]["submission_id"]

    response = client.post(
        "/api/v1/analyze",
        json={"submissions": submissions},
    )

    assert response.status_code == 422


def test_missing_source_code_is_rejected():
    submissions = sample_submissions()
    del submissions[0]["source_code"]

    response = client.post(
        "/api/v1/analyze",
        json={"submissions": submissions},
    )

    assert response.status_code == 422
