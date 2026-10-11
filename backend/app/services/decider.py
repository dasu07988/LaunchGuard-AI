from uuid import uuid4
from typing import Any

from app.services.policy import evaluate_policy


def make_decision(
    scenario: str,
    context: dict[str, Any],
) -> dict[str, Any]:
    policy_result = evaluate_policy(context)

    reasons = policy_result["reasons"]
    status = policy_result["decision"]
    risk_score = policy_result["risk_score"]

    if status == "needs_review":
        recommendations = [
            "Escalate the incident to the responsible engineer.",
            "Verify the incident severity and production impact.",
            "Review relevant logs and metrics before taking action.",
        ]
        reasoning = (
            "The policy rules identified conditions requiring "
            "human review. Do not take automated corrective action "
            "without further verification."
        )
    else:
        recommendations = [
            "Continue monitoring the service.",
            "Verify that the reported issue remains within acceptable limits.",
        ]
        reasoning = (
            "The configured policy rules did not trigger mandatory "
            "human review. Continue monitoring and follow operational procedures."
        )

    return {
        "decision_id": str(uuid4()),
        "status": status,
        "risk_score": risk_score,
        "confidence": 0.85 if context.get("severity") and context.get("environment") else 0.5,
        "reasoning": reasoning,
        "recommendations": recommendations,
        "policy_reasons": reasons,
        "requires_human_review": policy_result["requires_human_review"],
        "scenario": scenario,
    }
