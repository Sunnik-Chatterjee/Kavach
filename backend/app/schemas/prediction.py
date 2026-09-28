"""Prediction schemas."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PredictionCreate(BaseModel):
    """Payload for ingesting a new prediction from the ML layer."""

    fault_label: str = Field(..., min_length=1, max_length=128)
    confidence: float = Field(..., ge=0.0, le=1.0)
    probabilities_json: dict[str, Any] = Field(
        ...,
        description="Full label -> probability map.",
    )
    prediction_timestamp: datetime | None = Field(
        default=None,
        description="Time the ML layer produced the prediction. Defaults to now.",
    )


class PredictionRead(BaseModel):
    """Prediction as returned to the frontend."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    fault_label: str
    confidence: float
    probabilities_json: dict[str, Any]
    prediction_timestamp: datetime
    created_at: datetime


class PredictionStats(BaseModel):
    """Dashboard statistics derived from prediction history."""

    total_predictions: int
    normal_predictions: int
    fault_predictions: int
    fault_rate: float
    average_confidence: float