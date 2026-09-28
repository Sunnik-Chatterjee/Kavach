"""PredictionService.

Business logic for predictions: create, latest, history, and dashboard
statistics. Kept explicit and simple — no generic service layer.
"""

from app.repositories.prediction import PredictionRepository
from app.schemas.common import Paginated
from app.schemas.dashboard import DashboardSummary, FaultDistribution
from app.schemas.prediction import (
    PredictionCreate,
    PredictionRead,
    PredictionStats,
)
from app.websocket.manager import manager

# The EdgeAI model's non-fault class. Everything else counts as a fault.
NORMAL_LABEL = "healthy"


class PredictionService:
    """Orchestrates prediction persistence and queries."""

    def __init__(self, repository: PredictionRepository) -> None:
        self._repository = repository

    async def create_prediction(self, data: PredictionCreate) -> PredictionRead:
        """Persist a new prediction and return it as a read model."""
        prediction = await self._repository.create(data)
        prediction_read = PredictionRead.model_validate(prediction)
        
        # Broadcast prediction created event
        await manager.broadcast_prediction_created(
            prediction_read.model_dump(mode="json")
        )
        
        return prediction_read

    async def get_latest(self) -> PredictionRead | None:
        """Return the most recent prediction, or None if none exist."""
        prediction = await self._repository.get_latest()
        if prediction is None:
            return None
        return PredictionRead.model_validate(prediction)

    async def list_predictions(
        self,
        *,
        page: int,
        size: int,
        fault_label: str | None = None,
    ) -> Paginated[PredictionRead]:
        """Return a paginated list of predictions, newest-first."""
        items, total = await self._repository.list_paginated(
            page=page,
            size=size,
            fault_label=fault_label,
        )
        return Paginated[PredictionRead](
            total=total,
            page=page,
            size=size,
            items=[PredictionRead.model_validate(item) for item in items],
        )

    async def get_stats(self) -> PredictionStats:
        """Compute dashboard statistics from prediction history."""
        total = await self._repository.count()
        normal = await self._repository.count_by_label(NORMAL_LABEL)
        faults = total - normal
        fault_rate = (faults / total * 100.0) if total > 0 else 0.0
        avg_confidence = await self._repository.average_confidence()

        return PredictionStats(
            total_predictions=total,
            normal_predictions=normal,
            fault_predictions=faults,
            fault_rate=round(fault_rate, 2),
            average_confidence=round(avg_confidence * 100.0, 2),
        )

    async def get_dashboard_summary(self) -> DashboardSummary:
        """Build dashboard metrics with the newest prediction."""
        total, healthy, average_confidence = (
            await self._repository.get_dashboard_metrics(healthy_label=NORMAL_LABEL)
        )
        latest = await self._repository.get_latest()
        return DashboardSummary(
            total_predictions=total,
            healthy_count=healthy,
            fault_count=total - healthy,
            average_confidence=average_confidence,
            latest_prediction=PredictionRead.model_validate(latest)
            if latest is not None
            else None,
        )

    async def get_fault_distribution(self) -> FaultDistribution:
        """Return counts grouped by fault label."""
        counts = await self._repository.get_fault_distribution()
        return FaultDistribution(root=counts)