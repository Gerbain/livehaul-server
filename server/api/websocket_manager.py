"""api/websocket_manager.py — Manages WebSocket connections."""
import json, logging
from typing import Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self): self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept(); self.active.append(ws)
        logger.info(f"Client connected — total: {len(self.active)}")

    def disconnect(self, ws: WebSocket):
        if ws in self.active: self.active.remove(ws)
        logger.info(f"Client disconnected — total: {len(self.active)}")

    async def broadcast(self, message: dict[str, Any]):
        if not self.active: return
        payload = json.dumps(message)
        dead = []
        for ws in self.active:
            try: await ws.send_text(payload)
            except: dead.append(ws)
        for ws in dead: self.disconnect(ws)

    async def send_to(self, ws: WebSocket, message: dict[str, Any]):
        try: await ws.send_text(json.dumps(message))
        except: self.disconnect(ws)

    @property
    def count(self): return len(self.active)

manager = ConnectionManager()
