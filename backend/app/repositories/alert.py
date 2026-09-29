"""Database operations for alerts."""

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.core.constants import Severity
from app.models.alert import Alert


class AlertRepository:
    """Explicit data-access operations for the Alert entity."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind alert queries to the request-scoped database session."""
        self._session = session

    async def create(
        self,
        *,
        title: str,
        description: str,
        severity: Severity,
        source_device_id: str | None,
        event_type: str,
        confidence: float,
    ) -> Alert:
        """Persist and return a generated alert."""
        alert = Alert(
            title=title,
            description=description,
            severity=severity,
            source_device_id=source_device_id,
            event_type=event_type,
            confidence=confidence,
        )
        self._session.add(alert)
        await self._session.commit()
        await self._session.refresh(alert)
        return alert

    async def get_by_id(self, alert_id: uuid.UUID) -> Alert | None:
        """Return an alert by UUID, or None when it does not exist."""
        result = await self._session.execute(select(Alert).where(Alert.id == alert_id))
        return result.scalar_one_or_none()

    async def get_recent_unresolved(
        self, *, event_type: str, since: datetime
    ) -> Alert | None:
        """Find a matching unresolved alert created within the given window."""
        result = await self._session.execute(
            select(Alert)
            .where(
                Alert.event_type == event_type,
                Alert.resolved.is_(False),
                Alert.created_at >= since,
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def update_escalation(
        self,
        alert: Alert,
        *,
        severity: Severity,
        title: str,
        description: str,
        confidence: float,
    ) -> Alert:
        """Update an existing alert after a severity escalation."""
        alert.severity = severity
        alert.title = title
        alert.description = description
        alert.confidence = confidence
        await self._session.commit()
        await self._session.refresh(alert)
        return alert

    async def list_paginated(
        self,
        *,
        page: int,
        size: int,
        severity: Severity | None = None,
        acknowledged: bool | None = None,
        resolved: bool | None = None,
    ) -> tuple[list[Alert], int]:
        """Return newest-first alerts and total count matching the filters."""
        statement = select(Alert)
        count_statement = select(func.count()).select_from(Alert)
        filters: list[ColumnElement[bool]] = []
        if severity is not None:
            filters.append(Alert.severity == severity)
        if acknowledged is not None:
            filters.append(Alert.acknowledged == acknowledged)
        if resolved is not None:
            filters.append(Alert.resolved == resolved)
        if filters:
            statement = statement.where(*filters)
            count_statement = count_statement.where(*filters)

        total = (await self._session.execute(count_statement)).scalar_one()
        result = await self._session.execute(
            statement.order_by(Alert.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        return list(result.scalars().all()), total

    async def set_status(
        self, alert_id: uuid.UUID, *, acknowledged: bool = False, resolved: bool = False
    ) -> Alert | None:
        """Set lifecycle flags and return the updated alert, if found."""
        alert = await self.get_by_id(alert_id)
        if alert is None:
            return None
        if acknowledged:
            alert.acknowledged = True
        if resolved:
            alert.resolved = True
        await self._session.commit()
        await self._session.refresh(alert)
        return alert
