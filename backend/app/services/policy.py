from typing import Any


def evaluate_policy(context: dict[str, Any]) -> dict[str, Any]:
    environment = str(context.get("environment", "unknown")).lower()
    severity = str(context.get("severity", "unknown")).lower()

    risk_score = 0
    reasons: list[str] = []

    if environment == "production":
        risk_score += 40
        reasons.append("Production environment increases operational risk.")

    if severity == "critical":
        risk_score += 50
        reasons.append("Critical severity requires urgent attention.")
    elif severity == "high":
        risk_score += 35
        reasons.append("High severity requires careful evaluation.")
    elif severity == "medium":
        risk_score += 20
        reasons.append("Medium severity requires monitoring.")
    elif severity == "low":
        risk_score += 5
        reasons.append("Low severity has a lower initial risk weight.")
    else:
        reasons.append("Severity is unknown and needs verification.")

    risk_score = min(risk_score, 100)

    if environment == "unknown" or severity == "unknown":
        decision = "needs_review"
    elif risk_score >= 70:
        decision = "needs_review"
    else:
        decision = "approved"

    return {
        "risk_score": risk_score,
        "decision": decision,
        "reasons": reasons,
        "requires_human_review": decision == "needs_review",
    }
