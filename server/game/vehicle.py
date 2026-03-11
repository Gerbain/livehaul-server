"""game/vehicle.py — Vehicle model and movement."""
import math, uuid
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from server.routing.osrm import LatLng, Route

class VehicleStatus(str, Enum):
    IDLE = "idle"; EN_ROUTE = "en_route"; BROKEN_DOWN = "broken_down"; WAITING = "waiting"

@dataclass
class Vehicle:
    id: str; type: str; company_id: str; label: str; color: str
    speed_kmh: float; capacity_kg: float; icon: str
    lat: float = 0.0; lng: float = 0.0
    status: VehicleStatus = VehicleStatus.IDLE
    route: Optional[Route] = None
    route_index: int = 0; segment_progress: float = 0.0
    job_id: Optional[str] = None; speed_multiplier: float = 1.0
    total_distance_km: float = 0.0; total_deliveries: int = 0

    @classmethod
    def create(cls, vehicle_type, company_id, config, lat, lng):
        return cls(id=f"{vehicle_type}_{uuid.uuid4().hex[:6]}", type=vehicle_type,
            company_id=company_id, label=config["label"], color=config["color"],
            speed_kmh=config["speed_kmh"], capacity_kg=config["capacity_kg"],
            icon=config["icon"], lat=lat, lng=lng)

    def assign_route(self, route, job_id):
        self.route=route; self.route_index=1; self.segment_progress=0.0
        self.job_id=job_id; self.status=VehicleStatus.EN_ROUTE
        if route.waypoints: self.lat,self.lng = route.waypoints[0].lat, route.waypoints[0].lng

    def tick(self, delta_seconds):
        if self.status != VehicleStatus.EN_ROUTE or not self.route: return False
        if self.route_index >= len(self.route.waypoints): self._complete(); return True
        budget = (self.speed_kmh * self.speed_multiplier * 1000 / 3600) * delta_seconds
        while budget > 0 and self.route_index < len(self.route.waypoints):
            prev = self.route.waypoints[self.route_index-1]
            curr = self.route.waypoints[self.route_index]
            seg = _hav(prev, curr)
            if seg == 0: self.route_index += 1; continue
            rem = seg * (1.0 - self.segment_progress)
            if budget >= rem:
                budget -= rem; self.total_distance_km += rem/1000
                self.route_index += 1; self.segment_progress = 0.0
                if self.route_index >= len(self.route.waypoints):
                    last = self.route.waypoints[-1]; self.lat,self.lng = last.lat,last.lng
                    self._complete(); return True
            else:
                self.segment_progress += budget/seg; self.total_distance_km += budget/1000; budget=0
        if self.route_index < len(self.route.waypoints):
            p=self.route.waypoints[self.route_index-1]; c=self.route.waypoints[self.route_index]; t=self.segment_progress
            self.lat=p.lat+(c.lat-p.lat)*t; self.lng=p.lng+(c.lng-p.lng)*t
        return False

    def _complete(self):
        self.status=VehicleStatus.IDLE; self.route=None
        self.route_index=0; self.segment_progress=0.0; self.total_deliveries+=1; self.job_id=None

    def to_dict(self):
        return {"id":self.id,"type":self.type,"company_id":self.company_id,"label":self.label,
            "color":self.color,"icon":self.icon,"lat":round(self.lat,6),"lng":round(self.lng,6),
            "status":self.status.value,"job_id":self.job_id,"speed_multiplier":self.speed_multiplier,
            "total_distance_km":round(self.total_distance_km,2),"total_deliveries":self.total_deliveries}

def _hav(a,b):
    R=6_371_000; f1,f2=math.radians(a.lat),math.radians(b.lat)
    df,dl=math.radians(b.lat-a.lat),math.radians(b.lng-a.lng)
    x=math.sin(df/2)**2+math.cos(f1)*math.cos(f2)*math.sin(dl/2)**2
    return R*2*math.atan2(math.sqrt(x),math.sqrt(1-x))
