from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio

router = APIRouter()

# Active connections per user
connections = {}


@router.websocket("/ws/logs/{user_id}")
async def logs_ws(websocket: WebSocket, user_id: str):
    await websocket.accept()

    if user_id not in connections:
        connections[user_id] = []

    connections[user_id].append(websocket)

    print(f"[WS] Connected: {user_id}")

    try:
        while True:
            # Keep connection alive
            await asyncio.sleep(1)

    except WebSocketDisconnect:
        connections[user_id].remove(websocket)
        print(f"[WS] Disconnected: {user_id}")