"""Alert API schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, computed_field

from app.core.constants import Severity


class AlertRead(BaseModel):
    """Alert as returned to API clients."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str
    severity: Severity
    source_device_id: str | None
    event_type: str
    confidence: float
    created_at: datetime
    acknowledged: bool
    resolved: bool

    @computed_field
    @property
    def high_priority(self) -> bool:
        """Whether the alert requires immediate attention."""
        return self.severity in (Severity.HIGH, Severity.CRITICAL)
