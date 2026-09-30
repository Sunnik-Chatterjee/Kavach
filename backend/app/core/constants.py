"""Shared constants.

Event names, severity levels, fault labels, recommendation statuses, and
security event types used across the application.
"""

from enum import StrEnum


class EventType(StrEnum):
    """WebSocket event names broadcast to connected clients."""

    PREDICTION_CREATED = "PREDICTION_CREATED"
    ALERT_CREATED = "ALERT_CREATED"
    ALERT_RESOLVED = "ALERT_RESOLVED"
    RECOMMENDATION_CREATED = "RECOMMENDATION_CREATED"
    SECURITY_EVENT_CREATED = "SECURITY_EVENT_CREATED"


class Severity(StrEnum):
    """Severity levels for alerts and security events."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


ALERT_DEDUP_WINDOW_MINUTES = 5
CONFIDENCE_MEDIUM_THRESHOLD = 0.60
CONFIDENCE_HIGH_THRESHOLD = 0.80
CONFIDENCE_CRITICAL_THRESHOLD = 0.95
HEALTHY_LABELS = frozenset({"healthy", "normal"})
SEVERITY_RANK: dict[Severity, int] = {
    Severity.LOW: 0,
    Severity.MEDIUM: 1,
    Severity.HIGH: 2,
    Severity.CRITICAL: 3,
}
DEFAULT_CONFIDENCE_THRESHOLD: float = 0.8


class FaultLabel(StrEnum):
    """Machine condition classes produced by the ML model."""

    NORMAL = "normal"
    BEARING_FAULT = "bearing_fault"
    MOTOR_OVERLOAD = "motor_overload"
    MECHANICAL_IMBALANCE = "mechanical_imbalance"


class RecommendationStatus(StrEnum):
    """Lifecycle states for the human-in-the-loop workflow."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class SecurityEventType(StrEnum):
    """Types of abnormal machine behaviour tracked by the security module."""

    POWER_ANOMALY = "POWER_ANOMALY"
    UNAUTHORIZED_ACCESS = "UNAUTHORIZED_ACCESS"
    COMMUNICATION_ANOMALY = "COMMUNICATION_ANOMALY"
    SENSOR_TAMPERING = "SENSOR_TAMPERING"
