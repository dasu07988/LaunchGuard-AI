
import logging
from typing import Any
from uuid import uuid4

import httpx

from app.config import settings

from app.services.policy import evaluate_policy

logger = logging.getLogger(__name__)

DECIDER_URL = settings.decider_url

ALLOWED_ACTIONS = {
    "allow_read_only_check",
    "ask_for_clarification",
    "require_human_review",
}


def call_strands_decider(
    scenario: str,
    context: dict[str, Any],
) -> dict[str, Any]:
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
                    "Never authorize production changes solely from "
                    "this model output."
                ),
                "criteria": {
                    "allow_read_only_check": (
                        "Allow read-only diagnostic checks without "
                        "modifying infrastructure."
                    ),
                    "ask_for_clarification": (
                        "Request missing information before deciding."
                    ),
                    "require_human_review": (
                        "Require authorized human review before "
                        "further production changes."
                    ),
                },
            },
            "human_review": {
                "type": "noul",
                "instructions": (
                    "Does this situation require human review before "
                    "further changes?"
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

    confidence = float(choice_answer["confidence"])
    review_probability = float(review_answer["noul"])

    if not 0.0 <= confidence <= 1.0:
        raise ValueError("Invalid Decider confidence")

    if not 0.0 <= review_probability <= 1.0:
        raise ValueError("Invalid human-review probability")

    return {
        "model": result.get("model", "unknown"),
        "action": action,
        "choice_confidence": confidence,
        "probabilities": choice_answer.get("probabilities", {}),
        "human_review_probability": review_probability,
        "latency_ms": result.get("latency_ms"),
    }


def make_decision(
    scenario: str,
    context: dict[str, Any],
) -> dict[str, Any]:
    """
    Combine deterministic policies with Strands Decider 2B.

    Bedrock provides an optional explanation only. It cannot
    approve or change the safety decision.
    """

    policy_result = evaluate_policy(context)

    risk_score = policy_result["risk_score"]
    policy_reasons = list(policy_result["reasons"])

    # Obtain the decision from the local Strands Decider service.
    try:
        model_result = call_strands_decider(scenario, context)

    except Exception as exc:
        logger.warning(
            "Strands Decider unavailable: %s",
            type(exc).__name__,
        )

        model_result = None

        policy_reasons.append(
            "Strands Decider unavailable or returned invalid data: "
            f"{type(exc).__name__}."
        )

    # Fail closed if the decision model is unavailable.
    if model_result is None:
        status = "needs_review"
        requires_human_review = True
        action = "require_human_review"
        confidence = 0.0

        reasoning = (
            "The decision model could not be verified. Human review "
            "is required before proceeding. No infrastructure changes "
            "were executed."
        )

        recommendations = [
            "Check that the local Strands Decider service is running.",
            "Review the scenario and risk context manually.",
            "Do not perform production changes until an authorized "
            "reviewer approves.",
        ]

    else:
        action = model_result["action"]
        confidence = model_result["choice_confidence"]
        review_probability = model_result["human_review_probability"]

        # Deterministic safety policy always takes priority.
        policy_requires_review = policy_result["requires_human_review"]

        model_requires_review = (
            action == "require_human_review"
            or review_probability >= 0.5
        )

        low_confidence = confidence < 0.60

        requires_human_review = (
            policy_requires_review
            or model_requires_review
            or low_confidence
            or action == "ask_for_clarification"
        )

        if requires_human_review:
            status = "needs_review"

            reasoning = (
                "Human review is required based on the deterministic "
                "safety policy and/or the Strands Decider recommendation. "
                "Model output alone cannot authorize a production change."
            )

            recommendations = [
                "Review the incident with the responsible engineer.",
                "Verify severity, impact, logs, and recent configuration changes.",
                "Use read-only diagnostics until an authorized reviewer "
                "approves next steps.",
            ]

        else:
            # Approved means read-only diagnostics only.
            status = "approved"

            reasoning = (
                "The deterministic policy did not require review and "
                "the model did not trigger a review condition. This is "
                "not authorization to execute infrastructure changes."
            )

            recommendations = [
                "Limit activity to read-only diagnostic checks.",
                "Re-evaluate if the severity or environment changes.",
            ]

    # Build the safety result before requesting an explanation.
    decision = {
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
            model_result["human_review_probability"]
            if model_result
            else None
        ),
        "bedrock_explanation": None,
    }

    # Bedrock is optional and must never change the safety result.
    try:
        decision["bedrock_explanation"] = explain_decision(
            scenario=scenario,
            decision=decision,
        )

    except Exception as exc:
        logger.warning(
            "Bedrock explanation unavailable: %s",
            type(exc).__name__,
        )

    return decision
