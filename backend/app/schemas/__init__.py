"""Pydantic v2 schemas."""

from app.schemas.common import ErrorResponse, Paginated, SuccessResponse
from app.schemas.prediction import (
    PredictionCreate,
    PredictionRead,
    PredictionStats,
)

__all__ = [
    "ErrorResponse",
    "Paginated",
    "SuccessResponse",
    "PredictionCreate",
    "PredictionRead",
    "PredictionStats",
]