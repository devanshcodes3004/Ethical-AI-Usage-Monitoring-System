"""
schemas.py

Defines the Pydantic schemas used by the AI Governance Engine.

These schemas provide a structured representation of the governance
decision generated after analyzing a user's prompt.
"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class RiskLevel(str, Enum):
    """
    Overall severity level assigned to the prompt.
    """

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Decision(str, Enum):
    """
    Final governance decision.
    """

    ALLOW = "ALLOW"

    WARN = "WARN"

    BLOCK = "BLOCK"


class ModelProvider(str, Enum):
    """
    Target LLM selected by the governance engine.
    """

    GEMINI = "Gemini"

    OLLAMA = "Ollama"


class GovernanceDecision(BaseModel):
    """
    Structured governance output generated after analyzing
    a user's prompt.
    """

    model_config = ConfigDict(

        extra="forbid",

        validate_assignment=True,

        use_enum_values=False

    )

    risk_score: int = Field(
        ...,
        ge=0,
        le=100,
        description=(
            "Overall risk score assigned to the prompt."
        ),
        examples=[92],
    )

    risk_level: RiskLevel = Field(
        ...,
        description=(
            "Overall severity level."
        ),
        examples=["HIGH"],
    )

    decision: Decision = Field(
        ...,
        description=(
            "Final governance decision."
        ),
        examples=["BLOCK"],
    )

    selected_model: ModelProvider = Field(
        ...,
        description=(
            "Model selected to process the request."
        ),
        examples=["Ollama"],
    )

    categories: List[str] = Field(
        default_factory=list,
        description=(
            "List of detected governance or security categories."
        ),
        examples=[
            [
                "Prompt Injection",
                "Information Disclosure"
            ]
        ],
    )

    reason: str = Field(
        ...,
        min_length=10,
        max_length=300,
        description=(
            "Short explanation describing the governance decision."
        ),
        examples=[
            "The prompt attempts to override system instructions and reveal internal implementation details."
        ],
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description=(
            "Confidence score between 0.0 and 1.0."
        ),
        examples=[0.97],
    )

    sanitized_prompt: Optional[str] = Field(
        default=None,
        description=(
            "Prompt after masking or removing sensitive information."
        ),
        examples=[
            "My email is [EMAIL_REDACTED]"
        ],
    )