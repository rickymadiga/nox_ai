# routes/ws.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from flask import app
from nox_backend.core.security import decode_token
import logging

from fastapi import WebSocket

active_connections = []

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])

router = APIRouter(tags=["jobs"])


@router.websocket("/websocket")
async def websocket_endpoint(websocket: WebSocket):

    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=1008)
        return

    try:
        user = decode_token(token)  # must return user_id
        user_id = str(user).lower().strip()
    except Exception:
        await websocket.close(code=1008)
        return

    manager = websocket.app.state.ws_manager

    await manager.connect(user_id, websocket)

    try:
        while True:
            await websocket.receive_text()  # keep alive
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)


@router.websocket("/jobs")
async def websocket_jobs(ws: WebSocket):
    await ws.accept()
    active_connections.append(ws)

    try:
        while True:
            await ws.receive_text()  # keep alive
    except:
        active_connections.remove(ws)        