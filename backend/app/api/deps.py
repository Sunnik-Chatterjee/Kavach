"""Shared FastAPI dependencies (dependency injection).

Provides database sessions and service instances to route handlers.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.repositories.alert import AlertRepository
from app.repositories.prediction import PredictionRepository
from app.services.alert_service import AlertService
from app.services.prediction import PredictionService


async def get_prediction_repository(
    session: AsyncSession = Depends(get_db),
) -> PredictionRepository:
    """Provide a PredictionRepository bound to the request session."""
    return PredictionRepository(session)


async def get_alert_repository(
    session: AsyncSession = Depends(get_db),
) -> AlertRepository:
    """Provide an AlertRepository bound to the request session."""
    return AlertRepository(session)


async def get_alert_service(
    repository: AlertRepository = Depends(get_alert_repository),
) -> AlertService:
    """Provide an AlertService wired to the repository."""
    return AlertService(repository)


async def get_prediction_service(
    repository: PredictionRepository = Depends(get_prediction_repository),
    alert_service: AlertService = Depends(get_alert_service),
) -> PredictionService:
    """Provide a PredictionService wired to the repository."""
    return PredictionService(repository, alert_service)
