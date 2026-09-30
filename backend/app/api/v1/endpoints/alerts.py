"""Alert query and lifecycle endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_alert_service
from app.core.constants import Severity
from app.schemas.alert import AlertRead
from app.schemas.common import Paginated, SuccessResponse
from app.services.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=SuccessResponse[Paginated[AlertRead]])
async def list_alerts(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    severity: Severity | None = Query(None),
    acknowledged: bool | None = Query(None),
    resolved: bool | None = Query(None),
    service: AlertService = Depends(get_alert_service),
) -> SuccessResponse[Paginated[AlertRead]]:
    """Return a filtered page of alerts."""
    result = await service.list_alerts(
        page=page,
        size=size,
        severity=severity,
        acknowledged=acknowledged,
        resolved=resolved,
    )
    return SuccessResponse(message="Alerts fetched", data=result)


@router.get("/{alert_id}", response_model=SuccessResponse[AlertRead])
async def get_alert(
    alert_id: UUID,
    service: AlertService = Depends(get_alert_service),
) -> SuccessResponse[AlertRead]:
    """Return one alert by UUID."""
    alert = await service.get_alert(alert_id)
    return SuccessResponse(message="Alert fetched", data=alert)


@router.patch("/{alert_id}/acknowledge", response_model=SuccessResponse[AlertRead])
async def acknowledge_alert(
    alert_id: UUID,
    service: AlertService = Depends(get_alert_service),
) -> SuccessResponse[AlertRead]:
    """Mark an alert as acknowledged."""
    alert = await service.acknowledge_alert(alert_id)
    return SuccessResponse(message="Alert acknowledged", data=alert)


@router.patch("/{alert_id}/resolve", response_model=SuccessResponse[AlertRead])
async def resolve_alert(
    alert_id: UUID,
    service: AlertService = Depends(get_alert_service),
) -> SuccessResponse[AlertRead]:
    """Mark an alert as resolved."""
    alert = await service.resolve_alert(alert_id)
    return SuccessResponse(message="Alert resolved", data=alert)
