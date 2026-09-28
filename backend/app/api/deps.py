"""Shared FastAPI dependencies (dependency injection).

Provides database sessions and service instances to route handlers.
"""

from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.repositories.prediction import PredictionRepository
from app.services.prediction import PredictionService


async def get_prediction_repository(
    session: AsyncSession = Depends(get_db),
) -> PredictionRepository:
    """Provide a PredictionRepository bound to the request session."""
    return PredictionRepository(session)


async def get_prediction_service(
    repository: PredictionRepository = Depends(get_prediction_repository),
) -> PredictionService:
    """Provide a PredictionService wired to the repository."""
    return PredictionService(repository)