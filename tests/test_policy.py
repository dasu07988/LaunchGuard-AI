from app.services.policy import evaluate_policy


def test_production_high_severity_requires_review():
    result = evaluate_policy({
        "environment": "production",
        "severity": "high",
    })

    assert result["risk_score"] == 75
    assert result["decision"] == "needs_review"
    assert result["requires_human_review"] is True


def test_unknown_context_requires_review():
    result = evaluate_policy({})

    assert result["decision"] == "needs_review"
    assert result["requires_human_review"] is True


def test_low_severity_non_production():
    result = evaluate_policy({
        "environment": "development",
        "severity": "low",
    })

    assert result["risk_score"] == 5
    assert result["decision"] == "approved"
    assert result["requires_human_review"] is False
