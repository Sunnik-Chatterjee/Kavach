"""WebSocket endpoint.

Primary: /api/v1/ws
Alias:   /ws
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.websocket.manager import manager

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time prediction updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and receive messages if needed
            data = await websocket.receive_text()
            # Echo back for testing
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
