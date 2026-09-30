"""WebSocket package: connection manager, events, and endpoint."""

from app.websocket.manager import manager as manager
from app.websocket.router import router as router

__all__ = ["manager", "router"]
