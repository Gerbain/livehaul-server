"""
main.py — LiveHaul server entry point.

Endpoints:
  GET  /health               server + OSRM health
  GET  /api/state            full game state snapshot
  WS   /ws                   real-time WebSocket feed
  POST /admin/pause
  POST /admin/resume
  POST /admin/reload-configs
  POST /admin/add-money
  GET  /admin/vehicles
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from server.api.websocket_manager import manager
from server.config import cfg
from server.game.state import state
from server.routing.osrm import osrm

logging.basicConfig(
    level=getattr(logging, cfg.game["server"]["log_level"].upper(), logging.INFO),
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=== LiveHaul server starting ===")
    state.initialize()
    asyncio.create_task(state.start_loop())
    yield
    state.stop()
    logger.info("=== LiveHaul server stopped ===")


app = FastAPI(title="LiveHaul Server", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    osrm_ok = await osrm.health_check()
    return {
        "status":  "ok",
        "game":    "livehaul",
        "osrm":    "ok" if osrm_ok else "unreachable",
        "clients": manager.count,
        "tick":    state.tick_count,
        "paused":  state.paused,
    }


@app.get("/api/state")
async def get_state():
    return JSONResponse(state.get_snapshot())


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        await manager.send_to(ws, state.get_snapshot())
        while True:
            data = await ws.receive_text()
            logger.debug(f"WS message: {data}")
    except WebSocketDisconnect:
        manager.disconnect(ws)


@app.post("/admin/pause")
async def admin_pause():
    state.pause()
    return {"status": "paused"}

@app.post("/admin/resume")
async def admin_resume():
    state.resume()
    return {"status": "resumed"}

@app.post("/admin/reload-configs")
async def admin_reload():
    ok = cfg.reload()
    return {"status": "ok" if ok else "partial", "errors": cfg.errors}

@app.post("/admin/add-money")
async def admin_add_money(company_id: str, amount: float):
    state.add_money(company_id, amount)
    return {"status": "ok", "company": company_id, "amount": amount}

@app.get("/admin/vehicles")
async def admin_vehicles():
    return [v.to_dict() for v in state.vehicles.values()]
