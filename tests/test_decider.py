
from app.services import decider


def mock_model(action="allow_read_only_check", confidence=0.9, review_probability=0.1):
    return {
        "model": "strands-decider-2B-hobson-v21",
        "action": action,
        "choice_confidence": confidence,
        "probabilities": {
            "allow_read_only_check": 0.8,
            "ask_for_clarification": 0.1,
            "require_human_review": 0.1,
        },
        "human_review_probability": review_probability,
        "latency_ms": 100,
    }


def test_production_high_severity_requires_review(monkeypatch):
    monkeypatch.setattr(
        decider,
        "call_strands_decider",
        lambda scenario, context: mock_model(
            action="allow_read_only_check"
        ),
    )

    result = decider.make_decision(
        "Payment failures in production after a configuration change.",
        {"environment": "production", "severity": "high"},
    )

    assert result["status"] == "needs_review"
    assert result["requires_human_review"] is True
    assert result["risk_score"] == 75


def test_low_risk_can_allow_read_only_checks(monkeypatch):
    monkeypatch.setattr(
        decider,
        "call_strands_decider",
        lambda scenario, context: mock_model(),
    )

    result = decider.make_decision(
        "Check application health in development.",
        {"environment": "development", "severity": "low"},
    )

    assert result["status"] == "approved"
    assert result["requires_human_review"] is False
    assert result["decider_action"] == "allow_read_only_check"


def test_low_model_confidence_requires_review(monkeypatch):
    monkeypatch.setattr(
        decider,
        "call_strands_decider",
        lambda scenario, context: mock_model(confidence=0.4),
    )

    result = decider.make_decision(
        "Investigate an application issue.",
        {"environment": "development", "severity": "low"},
    )

    assert result["status"] == "needs_review"
    assert result["requires_human_review"] is True


def test_model_human_review_signal_requires_review(monkeypatch):
    monkeypatch.setattr(
        decider,
        "call_strands_decider",
        lambda scenario, context: mock_model(review_probability=0.8),
    )

    result = decider.make_decision(
        "Investigate a possible service failure.",
        {"environment": "development", "severity": "low"},
    )

    assert result["status"] == "needs_review"
    assert result["requires_human_review"] is True


def test_model_failure_fails_closed(monkeypatch):
    def unavailable_model(scenario, context):
        raise ConnectionError("Model service unavailable")

    monkeypatch.setattr(
        decider,
        "call_strands_decider",
        unavailable_model,
    )

    result = decider.make_decision(
        "Investigate a service incident.",
        {"environment": "development", "severity": "low"},
    )

    assert result["status"] == "needs_review"
    assert result["requires_human_review"] is True
    assert result["confidence"] == 0.0
    assert result["decider_model"] is None
