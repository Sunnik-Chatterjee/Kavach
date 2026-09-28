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


# Default confidence threshold (0-1) above which a fault triggers an alert.
DEFAULT_CONFIDENCE_THRESHOLD: float = 0.8