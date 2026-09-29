"""Alert evaluation, persistence, and notification orchestration."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.core.constants import (
    ALERT_DEDUP_WINDOW_MINUTES,
    CONFIDENCE_CRITICAL_THRESHOLD,
    CONFIDENCE_HIGH_THRESHOLD,
    CONFIDENCE_MEDIUM_THRESHOLD,
    HEALTHY_LABELS,
    SEVERITY_RANK,
    Severity,
)
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.models.alert import Alert
from app.repositories.alert import AlertRepository
from app.schemas.alert import AlertRead
from app.schemas.common import Paginated
from app.schemas.prediction import PredictionCreate
from app.websocket.manager import manager

logger = get_logger(__name__)

# Extend this mapping as new live event labels are introduced.
ALERT_DETAILS: dict[str, tuple[str, str]] = {
    "weapon_detected": (
        "Weapon Detected",
        "Possible weapon detected by camera.",
    ),
    "violence_detected": (
        "Violence Detected",
        "Possible violence detected by camera.",
    ),
    "intrusion_detected": (
        "Intrusion Detected",
        "Possible unauthorized entry detected.",
    ),
    "suspicious_activity": (
        "Suspicious Activity",
        "Suspicious activity detected by camera.",
    ),
}


class AlertService:
    """Evaluate live updates and manage generated alert records."""

    def __init__(self, repository: AlertRepository) -> None:
        """Bind alert operations to the request-scoped repository."""
        self._repository = repository

    async def process_live_update(self, data: PredictionCreate) -> AlertRead | None:
        """Evaluate a prediction and create, escalate, or suppress its alert."""
        event_type = self._event_type(data)
        if self._is_healthy_prediction(data, event_type):
            return None

        severity = self._determine_severity(data.confidence)
        if severity is None:
            self._log_low_confidence(event_type, data.confidence)
            return None

        title, description = self._alert_details(event_type)
        existing_alert = await self._find_duplicate_alert(event_type)
        if existing_alert is None:
            return await self._create_alert(
                data, event_type, severity, title, description
            )

        if not self._should_escalate(existing_alert.severity, severity):
            self._log_duplicate(existing_alert, event_type, severity)
            return None

        return await self._escalate_alert(
            existing_alert, event_type, severity, title, description, data.confidence
        )

    @staticmethod
    def _event_type(prediction_data: PredictionCreate) -> str:
        """Return the normalized explicit event type or fault label."""
        return (
            (prediction_data.event_type or prediction_data.fault_label).strip().lower()
        )

    @staticmethod
    def _is_healthy_prediction(
        prediction_data: PredictionCreate, event_type: str
    ) -> bool:
        """Exclude healthy labels regardless of their confidence score."""
        fault_label = prediction_data.fault_label.strip().lower()
        return fault_label in HEALTHY_LABELS or event_type in HEALTHY_LABELS

    @staticmethod
    def _determine_severity(confidence: float) -> Severity | None:
        """Map confidence to severity, returning None below the alert threshold."""
        if confidence < CONFIDENCE_MEDIUM_THRESHOLD:
            return None
        if confidence >= CONFIDENCE_CRITICAL_THRESHOLD:
            return Severity.CRITICAL
        if confidence >= CONFIDENCE_HIGH_THRESHOLD:
            return Severity.HIGH
        return Severity.MEDIUM

    @staticmethod
    def _alert_details(event_type: str) -> tuple[str, str]:
        """Return configured display text or a generic event description."""
        return ALERT_DETAILS.get(
            event_type,
            (event_type.replace("_", " ").title(), "Suspicious event detected."),
        )

    async def _find_duplicate_alert(self, event_type: str) -> Alert | None:
        """Find a matching unresolved alert inside the configured time window."""
        deduplication_cutoff = datetime.now(timezone.utc) - timedelta(
            minutes=ALERT_DEDUP_WINDOW_MINUTES
        )
        return await self._repository.get_recent_unresolved(
            event_type=event_type,
            since=deduplication_cutoff,
        )

    @staticmethod
    def _should_escalate(
        existing_severity: Severity, incoming_severity: Severity
    ) -> bool:
        """Return whether the incoming severity ranks above the active alert."""
        return SEVERITY_RANK[incoming_severity] > SEVERITY_RANK[existing_severity]

    async def _create_alert(
        self,
        prediction_data: PredictionCreate,
        event_type: str,
        severity: Severity,
        title: str,
        description: str,
    ) -> AlertRead:
        """Persist a new alert, log it, and broadcast its creation."""
        alert_record = await self._repository.create(
            title=title,
            description=description,
            severity=severity,
            source_device_id=prediction_data.source_device_id,
            event_type=event_type,
            confidence=prediction_data.confidence,
        )
        alert_read = AlertRead.model_validate(alert_record)
        logger.info(
            "Alert created",
            extra={
                "alert_id": str(alert_record.id),
                "event_type": event_type,
                "severity": severity.value,
                "confidence": prediction_data.confidence,
            },
        )
        await self._broadcast_created_alert(alert_read)
        return alert_read

    async def _escalate_alert(
        self,
        existing_alert: Alert,
        event_type: str,
        severity: Severity,
        title: str,
        description: str,
        confidence: float,
    ) -> AlertRead:
        """Update the existing alert and broadcast its severity escalation."""
        previous_severity = existing_alert.severity
        alert_record = await self._repository.update_escalation(
            existing_alert,
            severity=severity,
            title=title,
            description=description,
            confidence=confidence,
        )
        alert_read = AlertRead.model_validate(alert_record)
        logger.info(
            "Alert escalated",
            extra={
                "alert_id": str(alert_record.id),
                "event_type": event_type,
                "previous_severity": previous_severity.value,
                "severity": severity.value,
                "confidence": confidence,
            },
        )
        await self._broadcast_updated_alert(alert_read)
        return alert_read

    @staticmethod
    def _log_low_confidence(event_type: str, confidence: float) -> None:
        """Log a structured skip when confidence is below the alert threshold."""
        logger.info(
            "Alert skipped because of low confidence",
            extra={"event_type": event_type, "confidence": confidence},
        )

    @staticmethod
    def _log_duplicate(
        existing_alert: Alert, event_type: str, incoming_severity: Severity
    ) -> None:
        """Log a structured skip when an alert is duplicate or less severe."""
        logger.info(
            "Alert skipped because of duplicate",
            extra={
                "event_type": event_type,
                "existing_alert_id": str(existing_alert.id),
                "existing_severity": existing_alert.severity.value,
                "incoming_severity": incoming_severity.value,
            },
        )

    @staticmethod
    async def _broadcast_created_alert(alert_read: AlertRead) -> None:
        """Send a newly created alert through the shared websocket manager."""
        await manager.broadcast_alert_created(alert_read.model_dump(mode="json"))

    @staticmethod
    async def _broadcast_updated_alert(alert_read: AlertRead) -> None:
        """Send an escalated alert through the shared websocket manager."""
        updated_payload = alert_read.model_dump(mode="json")
        updated_payload["timestamp"] = datetime.now(timezone.utc).isoformat()
        await manager.broadcast_alert_updated(updated_payload)

    async def get_alert(self, alert_id: UUID) -> AlertRead:
        alert = await self._repository.get_by_id(alert_id)
        if alert is None:
            raise NotFoundError("Alert not found")
        return AlertRead.model_validate(alert)

    async def list_alerts(
        self,
        *,
        page: int,
        size: int,
        severity: Severity | None = None,
        acknowledged: bool | None = None,
        resolved: bool | None = None,
    ) -> Paginated[AlertRead]:
        alerts, total = await self._repository.list_paginated(
            page=page,
            size=size,
            severity=severity,
            acknowledged=acknowledged,
            resolved=resolved,
        )
        return Paginated[AlertRead](
            total=total,
            page=page,
            size=size,
            items=[AlertRead.model_validate(alert) for alert in alerts],
        )

    async def acknowledge_alert(self, alert_id: UUID) -> AlertRead:
        alert = await self._repository.set_status(alert_id, acknowledged=True)
        if alert is None:
            raise NotFoundError("Alert not found")
        return AlertRead.model_validate(alert)

    async def resolve_alert(self, alert_id: UUID) -> AlertRead:
        alert = await self._repository.set_status(alert_id, resolved=True)
        if alert is None:
            raise NotFoundError("Alert not found")
        return AlertRead.model_validate(alert)
