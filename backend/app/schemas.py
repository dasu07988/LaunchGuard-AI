from typing import Any, Literal

from pydantic import BaseModel, Field


class DecisionRequest(BaseModel):
    scenario: str = Field(
        min_length=10,
        max_length=5000,
        description="Describe the decision that needs to be evaluated.",
    )
    context: dict[str, Any] = Field(default_factory=dict)


class DecisionResponse(BaseModel):
    decision_id: str
    status: Literal["approved", "rejected", "needs_review"]
    confidence: float = Field(ge=0, le=1)
    reasoning: str
    recommendations: list[str] = Field(default_factory=list)
    requires_human_review: bool = True
