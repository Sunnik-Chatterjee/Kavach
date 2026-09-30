"""Prediction endpoints.

GET /predictions/latest
GET /predictions
GET /predictions/stats
"""

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_prediction_service
from app.core.exceptions import NotFoundError
from app.schemas.common import Paginated, SuccessResponse
from app.schemas.prediction import PredictionRead, PredictionStats
from app.services.prediction import PredictionService

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get("/latest", response_model=SuccessResponse[PredictionRead])
async def get_latest_prediction(
    service: PredictionService = Depends(get_prediction_service),
) -> SuccessResponse[PredictionRead]:
    """Return the most recent prediction."""
    prediction = await service.get_latest()
    if prediction is None:
        raise NotFoundError("No predictions found yet")
    return SuccessResponse[PredictionRead](
        message="Latest prediction fetched",
        data=prediction,
    )


@router.get("", response_model=SuccessResponse[Paginated[PredictionRead]])
async def list_predictions(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    fault_label: str | None = Query(None),
    service: PredictionService = Depends(get_prediction_service),
) -> SuccessResponse[Paginated[PredictionRead]]:
    """Return a paginated list of predictions, optionally filtered by label."""
    result = await service.list_predictions(
        page=page,
        size=size,
        fault_label=fault_label,
    )
    return SuccessResponse[Paginated[PredictionRead]](
        message="Predictions fetched",
        data=result,
    )


@router.get("/stats", response_model=SuccessResponse[PredictionStats])
async def get_prediction_stats(
    service: PredictionService = Depends(get_prediction_service),
) -> SuccessResponse[PredictionStats]:
    """Return dashboard statistics derived from prediction history."""
    stats = await service.get_stats()
    return SuccessResponse[PredictionStats](
        message="Prediction statistics fetched",
        data=stats,
    )
