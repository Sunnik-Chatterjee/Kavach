"""Internal ingestion endpoints.

POST /internal/* — used by the ML inference service and hardware layer,
not by the frontend. Drives the end-to-end pipeline.
"""

from fastapi import APIRouter, Depends, status

from app.api.deps import get_prediction_service
from app.core.security import verify_api_key
from app.schemas.common import SuccessResponse
from app.schemas.prediction import PredictionCreate, PredictionRead
from app.services.prediction import PredictionService

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post(
    "/predictions",
    response_model=SuccessResponse[PredictionRead],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_api_key)],
)
async def ingest_prediction(
    payload: PredictionCreate,
    service: PredictionService = Depends(get_prediction_service),
) -> SuccessResponse[PredictionRead]:
    """Ingest a new prediction from the ML inference service.

    Validates the payload, persists it, and returns the stored prediction.
    No ML inference, feature extraction, or telemetry processing happens here.
    """
    prediction = await service.create_prediction(payload)
    return SuccessResponse[PredictionRead](
        message="Prediction ingested successfully",
        data=prediction,
    )
