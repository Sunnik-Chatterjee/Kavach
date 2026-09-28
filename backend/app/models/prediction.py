"""Prediction ORM model.

The single business entity of the backend. Records one ML inference result
produced by the EdgeAI inference service.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin, UUIDMixin


class Prediction(UUIDMixin, TimestampMixin, Base):
    """A single machine-learning prediction from the EdgeAI layer."""

    __tablename__ = "predictions"

    fault_label: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
        comment="Predicted fault class (from model.classes_).",
    )
    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Confidence of the top class (0-1).",
    )
    probabilities_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        comment="Full label -> probability map.",
    )
    prediction_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Time the ML layer produced the prediction.",
    )