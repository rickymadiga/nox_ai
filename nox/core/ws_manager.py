from typing import Dict, List
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections = {}  # user_id -> list

    async def connect(self, user_id, websocket):
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = []

        self.active_connections[user_id].append(websocket)

    def disconnect(self, user_id, websocket):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)

    async def send_to_user(self, user_id, data):
        for ws in self.active_connections.get(user_id, []):
            await ws.send_json(data)