"""Aggregates all v1 routers into a single APIRouter."""

from fastapi import APIRouter

from app.api.v1.endpoints import alerts, dashboard, health, ingestion, predictions
from app.websocket.router import router as websocket_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(predictions.router)
api_router.include_router(alerts.router)
api_router.include_router(ingestion.router)
api_router.include_router(dashboard.router)
api_router.include_router(websocket_router)
