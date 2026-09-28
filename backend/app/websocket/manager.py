"""ConnectionManager.

Handles connect, disconnect, and broadcast for WebSocket clients.

The module-level ``manager`` singleton should be imported everywhere so
that the same active-connections list is shared by the router (which
accepts sockets) and the service layer (which broadcasts events).
"""

from typing import Any
from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections and broadcasts messages to clients."""

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Any) -> None:
        """Send a message to all connected clients."""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                # Remove broken connections.
                self.active_connections.remove(connection)

    async def broadcast_prediction_created(self, prediction_data: Any) -> None:
        """Broadcast a prediction created event to all connected clients."""
        event = {
            "event": "PREDICTION_CREATED",
            "data": prediction_data,
        }
        await self.broadcast(event)


# Shared singleton — import this everywhere that needs to connect or
# broadcast over WebSockets.
manager = ConnectionManager()