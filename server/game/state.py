"""
game/state.py — Central game state and main loop.
"""

import asyncio
import logging
import time

from server.api.websocket_manager import manager
from server.config import cfg
from server.game.vehicle import Vehicle, VehicleStatus
from server.routing.osrm import LatLng, OSRMError, osrm

logger = logging.getLogger(__name__)

BRUSSELS = LatLng(lat=50.8503, lng=4.3517)
ANTWERP  = LatLng(lat=51.2194, lng=4.4025)


class GameState:
    def __init__(self):
        self.vehicles:   dict[str, Vehicle] = {}
        self.companies:  dict[str, dict]    = {}
        self.paused:     bool  = False
        self.tick_count: int   = 0
        self.game_time:  float = 0.0
        self._last_tick: float = time.monotonic()
        self._running:   bool  = False

    def initialize(self):
        companies_cfg = cfg.multiplayer.get("multiplayer", {}).get("companies", {})
        for company_id, data in companies_cfg.items():
            self.companies[company_id] = {
                "id":          company_id,
                "name":        data["name"],
                "color":       data["color"],
                "balance":     data.get("starting_money", 10000),
                "xp":          0,
                "level":       1,
                "vehicle_ids": [],
            }

        vehicles_cfg  = cfg.vehicles.get("vehicles", {})
        starting      = cfg.economy.get("economy", {}).get("starting_vehicles", [])
        first_company = next(iter(self.companies), None)
        center        = cfg.map["map"]["default_center"]

        if first_company:
            for v_def in starting:
                v_type = v_def["type"]
                v_cfg  = vehicles_cfg.get(v_type)
                if not v_cfg:
                    logger.warning(f"Unknown vehicle type: {v_type}")
                    continue
                vehicle = Vehicle.create(v_type, first_company, v_cfg, center["lat"], center["lng"])
                self.vehicles[vehicle.id] = vehicle
                self.companies[first_company]["vehicle_ids"].append(vehicle.id)
                logger.info(f"Spawned: {vehicle.id} → {first_company}")

    async def start_loop(self):
        self._running = True
        tick_rate = cfg.game["game"]["tick_rate"]
        logger.info(f"LiveHaul game loop started (tick every {tick_rate}s)")
        await self._demo_route()
        while self._running:
            await asyncio.sleep(tick_rate)
            await self.tick()

    async def tick(self):
        if self.paused:
            return
        now   = time.monotonic()
        delta = now - self._last_tick
        self._last_tick = now
        self.tick_count += 1
        self.game_time  += delta * cfg.game["game"]["time_scale"]

        for vehicle in self.vehicles.values():
            if vehicle.tick(delta):
                logger.info(f"{vehicle.id} completed route")

        await manager.broadcast({
            "type":      "game_tick",
            "tick":      self.tick_count,
            "game_time": self.game_time,
            "vehicles":  [v.to_dict() for v in self.vehicles.values()],
            "companies": list(self.companies.values()),
        })

    async def _demo_route(self):
        idle = next((v for v in self.vehicles.values() if v.status == VehicleStatus.IDLE), None)
        if not idle:
            return
        try:
            route = await osrm.get_route(BRUSSELS, ANTWERP)
            idle.assign_route(route, job_id="demo_1")
            logger.info(f"Demo route → {idle.id}: {route.distance_km:.1f}km, {len(route.waypoints)} waypoints")
        except OSRMError as e:
            logger.warning(f"OSRM unavailable for demo route: {e}")

    def get_snapshot(self) -> dict:
        return {
            "type":       "state_snapshot",
            "tick":       self.tick_count,
            "game_time":  self.game_time,
            "paused":     self.paused,
            "vehicles":   [v.to_dict() for v in self.vehicles.values()],
            "companies":  list(self.companies.values()),
            "map_config": {
                "center": cfg.map["map"]["default_center"],
                "zoom":   cfg.map["map"]["default_zoom"],
            },
        }

    def add_money(self, company_id: str, amount: float):
        if company_id in self.companies:
            self.companies[company_id]["balance"] += amount

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False
        self._last_tick = time.monotonic()

    def stop(self):
        self._running = False


state = GameState()
