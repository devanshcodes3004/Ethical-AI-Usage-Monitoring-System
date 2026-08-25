"""
models.py

Pydantic models representing MongoDB documents.
"""

from datetime import datetime, UTC
from typing import List, Optional

from pydantic import BaseModel, Field


class UserDocument(BaseModel):

    username: str

    email: str

    password: str

    role: str = "USER"

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    last_login: Optional[datetime] = None


class SessionDocument(BaseModel):

    user_id: str

    title: str

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    is_deleted: bool = False


class MessageDocument(BaseModel):

    session_id: str

    user_id: str

    role: str

    content: str

    model: Optional[str] = None

    latency: Optional[float] = None

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )


class AuditLogDocument(BaseModel):

    session_id: str

    user_id: str

    message_id: str

    risk_score: int

    risk_level: str

    decision: str

    categories: List[str]

    reason: str

    confidence: float

    selected_model: str

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )