"""routing/osrm.py — OSRM HTTP client wrapper."""
import logging
from dataclasses import dataclass
import httpx
from server.config import cfg

logger = logging.getLogger(__name__)

@dataclass
class LatLng:
    lat: float
    lng: float
    def to_osrm(self): return f"{self.lng},{self.lat}"

@dataclass
class Route:
    waypoints: list
    distance_m: float
    duration_s: float
    @property
    def distance_km(self): return self.distance_m / 1000

class OSRMError(Exception): pass

class OSRMClient:
    def __init__(self):
        c = cfg.map["osrm"]
        self.base_url = f"http://{c['host']}:{c['port']}"
        self.profile = c.get("profile","car")
        self.timeout = c.get("timeout_seconds",10)

    async def get_route(self, origin: LatLng, destination: LatLng) -> Route:
        url = f"{self.base_url}/route/v1/{self.profile}/{origin.to_osrm()};{destination.to_osrm()}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.get(url, params={"overview":"full","geometries":"geojson","steps":"false"})
                resp.raise_for_status()
            except httpx.ConnectError:
                raise OSRMError(f"Cannot connect to OSRM at {self.base_url}")
        data = resp.json()
        if data.get("code") != "Ok":
            raise OSRMError(f"OSRM: {data.get('message', data.get('code'))}")
        r = data["routes"][0]
        waypoints = [LatLng(lat=c[1], lng=c[0]) for c in r["geometry"]["coordinates"]]
        return Route(waypoints=waypoints, distance_m=r["distance"], duration_s=r["duration"])

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3) as c:
                return (await c.get(self.base_url)).status_code < 500
        except: return False

osrm = OSRMClient()
