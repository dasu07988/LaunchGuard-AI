
import os
from uuid import uuid4
from typing import Any

import httpx

from app.services.policy import evaluate_policy


DECIDER_URL = os.getenv(
    "DECIDER_URL",
    "http://127.0.0.1:8001/v1/systemone",
)

ALLOWED_ACTIONS = {
    "allow_read_only_check",
    "ask_for_clarification",
    "require_human_review",
}


def call_strands_decider(scenario: str, context: dict[str, Any]) -> dict[str, Any]:
    """Get a typed decision from the local Strands Decider service."""

    state = (
        f"Scenario: {scenario}\n"
        f"Environment: {context.get('environment', 'unknown')}\n"
        f"Severity: {context.get('severity', 'unknown')}\n"
        f"Context: {context}"
    )

    payload = {
        "state": state,
        "questions": {
            "next_action": {
                "type": "choice",
                "instructions": (
                    "Choose the safest next action. "
                    "Never authorize production changes solely from this model output."
                ),
                "criteria": {
                    "allow_read_only_check": (
                        "Allow read-only diagnostic checks without modifying infrastructure."
                    ),
                    "ask_for_clarification": (
                        "Request missing information before deciding."
                    ),
                    "require_human_review": (
                        "Require authorized human review before further production changes."
                    ),
                },
            },
            "human_review": {
                "type": "noul",
                "instructions": (
                    "Does this situation require human review before further changes?"
                ),
            },
        },
    }

    with httpx.Client(timeout=60.0) as client:
        response = client.post(DECIDER_URL, json=payload)
        response.raise_for_status()
        result = response.json()

    answers = result["answers"]
    choice_answer = answers["next_action"]
    review_answer = answers["human_review"]

    action = choice_answer["choice"]
    if action not in ALLOWED_ACTIONS:
        raise ValueError(f"Unexpected Decider action: {action}")

    return {
        "model": result.get("model", "unknown"),
        "action": action,
        "choice_confidence": float(choice_answer["confidence"]),
        "probabilities": choice_answer["probabilities"],
        "human_review_probability": float(review_answer["noul"]),
        "latency_ms": result.get("latency_ms"),
    }


def make_decision(scenario: str, context: dict[str, Any]) -> dict[str, Any]:
    """Combine model recommendations with deterministic safety policies."""

    policy_result = evaluate_policy(context)
    risk_score = policy_result["risk_score"]
    policy_reasons = list(policy_result["reasons"])

    try:
        model_result = call_strands_decider(scenario, context)
        model_available = True
    except Exception as exc:
        # Fail closed: an unavailable or invalid model must not approve changes.
        model_result = None
        model_available = False
        policy_reasons.append(
            f"Strands Decider unavailable or returned invalid data: "
            f"{type(exc).__name__}."
        )

    if not model_available:
        status = "needs_review"
        requires_human_review = True
        reasoning = (
            "The decision model could not be verified. Human review is required "
            "before proceeding. No infrastructure changes were executed."
        )
        recommendations = [
            "Check that the local Strands Decider service is running.",
            "Review the scenario and risk context manually.",
            "Do not perform production changes until an authorized reviewer approves.",
        ]
        action = "require_human_review"
        confidence = 0.0

    else:
        action = model_result["action"]
        confidence = model_result["choice_confidence"]
        review_probability = model_result["human_review_probability"]

        # Deterministic policy overrides model recommendations for high risk.
        policy_requires_review = policy_result["requires_human_review"]
        model_requires_review = (
            action == "require_human_review"
            or review_probability >= 0.5
        )

        # Low choice confidence also requires review instead of automatic approval.
        low_confidence = confidence < 0.60

        requires_human_review = (
            policy_requires_review or model_requires_review or low_confidence
        )

        if requires_human_review:
            status = "needs_review"
            reasoning = (
                "Human review is required based on the deterministic safety policy "
                "and/or the Strands Decider recommendation. Model output alone "
                "cannot authorize a production change."
            )
            recommendations = [
                "Review the incident with the responsible engineer.",
                "Verify severity, impact, logs, and recent configuration changes.",
                "Use read-only diagnostics until an authorized reviewer approves next steps.",
            ]
        elif action == "ask_for_clarification":
            status = "needs_review"
            requires_human_review = True
            reasoning = (
                "The model requested clarification. Gather the missing information "
                "before deciding whether to proceed."
            )
            recommendations = [
                "Collect the missing incident details.",
                "Re-evaluate the decision after the context is verified.",
            ]
        else:
            status = "approved"
            reasoning = (
                "The deterministic policy did not require review and the model "
                "did not trigger a review condition. This is not authorization "
                "to execute infrastructure changes."
            )
            recommendations = [
                "Limit activity to read-only diagnostic checks.",
                "Re-evaluate if the severity or environment changes.",
            ]

    return {
        "decision_id": str(uuid4()),
        "status": status,
        "risk_score": risk_score,
        "confidence": confidence,
        "reasoning": reasoning,
        "recommendations": recommendations,
        "policy_reasons": policy_reasons,
        "requires_human_review": requires_human_review,
        "scenario": scenario,
        "decider_action": action,
        "decider_model": (
            model_result["model"] if model_result else None
        ),
        "decider_probabilities": (
            model_result["probabilities"] if model_result else {}
        ),
        "human_review_probability": (
            model_result["human_review_probability"] if model_result else None
        ),
    }
