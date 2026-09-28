"""Health check endpoint.

GET /health — verifies backend availability.
"""

from datetime import datetime, timezone

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> JSONResponse:
    """Return backend availability status."""
    return JSONResponse(
        content={
            "success": True,
            "message": "Backend is healthy",
            "data": {
                "status": "UP",
                "version": settings.app_version,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }
    )