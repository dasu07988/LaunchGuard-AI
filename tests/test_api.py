
from fastapi.testclient import TestClient

from app.main import app
from app.services import decider


client = TestClient(app)


def mock_decision(scenario, context):
    return {
        "status": "approved",
        "requires_human_review": False,
        "risk_score": 5,
        "decider_action": "allow_read_only_check",
        "confidence": 0.94,
        "decider_model": "strands-decider-2B-hobson-v21",
    }


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "running"
    assert response.json()["docs"] == "/docs"


def test_create_decision(monkeypatch):
    monkeypatch.setattr(
        "app.main.make_decision",
        mock_decision,
    )

    response = client.post(
        "/api/v1/decisions",
        json={
            "scenario": "Check application health using read-only diagnostics.",
            "context": {
                "environment": "development",
                "severity": "low",
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "approved"
    assert response.json()["risk_score"] == 5
    assert response.json()["requires_human_review"] is False


def test_preview_decision(monkeypatch):
    monkeypatch.setattr(
        "app.main.make_decision",
        mock_decision,
    )

    response = client.post(
        "/api/v1/decisions/preview",
        json={
            "scenario": "Review development logs.",
            "context": {
                "environment": "development",
                "severity": "low",
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["decider_action"] == "allow_read_only_check"


def test_invalid_request_returns_422():
    response = client.post(
        "/api/v1/decisions",
        json={
            "scenario": "",
            "context": {},
        },
    )

    assert response.status_code == 422
