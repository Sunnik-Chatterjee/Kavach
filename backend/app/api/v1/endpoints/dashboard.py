"""Dashboard summary and fault distribution endpoints."""

from fastapi import APIRouter, Depends

from app.api.deps import get_prediction_service
from app.schemas.dashboard import DashboardSummary, FaultDistribution
from app.services.prediction import PredictionService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    service: PredictionService = Depends(get_prediction_service),
) -> DashboardSummary:
    """Return aggregate prediction metrics and the latest prediction."""
    return await service.get_dashboard_summary()


@router.get("/fault-distribution", response_model=FaultDistribution)
async def get_fault_distribution(
    service: PredictionService = Depends(get_prediction_service),
) -> FaultDistribution:
    """Return prediction counts grouped by fault label."""
    return await service.get_fault_distribution()