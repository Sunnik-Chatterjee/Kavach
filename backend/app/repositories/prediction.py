"""Prediction repository.

Explicit database operations for predictions. No business logic.
"""

from datetime import datetime

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prediction import Prediction
from app.schemas.prediction import PredictionCreate


class PredictionRepository:
    """Data-access operations for the Prediction entity."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind prediction queries to the request-scoped database session."""
        self._session = session

    async def create(self, data: PredictionCreate) -> Prediction:
        """Persist a new prediction and return it."""
        prediction = Prediction(
            fault_label=data.fault_label,
            confidence=data.confidence,
            probabilities_json=data.probabilities_json,
            prediction_timestamp=data.prediction_timestamp or datetime.utcnow(),
        )
        self._session.add(prediction)
        await self._session.commit()
        await self._session.refresh(prediction)
        return prediction

    async def get_latest(self) -> Prediction | None:
        """Return the most recent prediction, or None if none exist."""
        result = await self._session.execute(
            select(Prediction).order_by(Prediction.prediction_timestamp.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    async def list_paginated(
        self,
        *,
        page: int,
        size: int,
        fault_label: str | None = None,
    ) -> tuple[list[Prediction], int]:
        """Return a page of predictions and the total count.

        Filters by fault_label when provided. Ordered newest-first.
        """
        prediction_statement = select(Prediction)
        count_statement = select(func.count()).select_from(Prediction)
        if fault_label:
            prediction_statement = prediction_statement.where(
                Prediction.fault_label == fault_label
            )
            count_statement = count_statement.where(
                Prediction.fault_label == fault_label
            )

        total_count = (await self._session.execute(count_statement)).scalar_one()
        result = await self._session.execute(
            prediction_statement.order_by(Prediction.prediction_timestamp.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        return list(result.scalars().all()), total_count

    async def count(self) -> int:
        """Return the total number of predictions."""
        result = await self._session.execute(
            select(func.count()).select_from(Prediction)
        )
        return result.scalar_one()

    async def count_by_label(self, fault_label: str) -> int:
        """Return the number of predictions for a given fault label."""
        result = await self._session.execute(
            select(func.count())
            .select_from(Prediction)
            .where(Prediction.fault_label == fault_label)
        )
        return result.scalar_one()

    async def average_confidence(self) -> float:
        """Return the mean confidence across all predictions (0 if none)."""
        result = await self._session.execute(select(func.avg(Prediction.confidence)))
        avg = result.scalar_one()
        return float(avg) if avg is not None else 0.0

    async def get_dashboard_metrics(
        self,
        *,
        healthy_label: str,
    ) -> tuple[int, int, float]:
        """Return total count, healthy count, and average confidence."""
        statement = select(
            func.count(Prediction.id),
            func.coalesce(
                func.sum(
                    case(
                        (Prediction.fault_label == healthy_label, 1),
                        else_=0,
                    )
                ),
                0,
            ),
            func.coalesce(func.avg(Prediction.confidence), 0.0),
        )
        result = await self._session.execute(statement)
        total, healthy, average_confidence = result.one()
        return int(total), int(healthy), float(average_confidence)

    async def get_fault_distribution(self) -> dict[str, int]:
        """Return prediction counts grouped by fault label."""
        statement = select(
            Prediction.fault_label,
            func.count(Prediction.id),
        ).group_by(Prediction.fault_label)
        result = await self._session.execute(statement)
        return {label: int(count) for label, count in result.all()}
