"""Alert ORM model."""

from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import Severity
from app.database.base import Base, UUIDMixin


class Alert(UUIDMixin, Base):
    """A generated alert for a non-low-severity live update."""

    __tablename__ = "alerts"

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=False)
    severity: Mapped[Severity] = mapped_column(
        Enum(Severity, name="alert_severity"), nullable=False, index=True
    )
    source_device_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    acknowledged: Mapped[bool] = mapped_column(
        default=False, server_default="false", nullable=False
    )
    resolved: Mapped[bool] = mapped_column(
        default=False, server_default="false", nullable=False
    )
