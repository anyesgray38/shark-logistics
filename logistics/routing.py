"""Provider-independent routing primitives for Build 02.

The core engine uses geodesic distance and a configurable travel-speed model.
External routing providers can later implement RouteProvider without changing
business logic.
"""

from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt
from typing import Protocol

from .models import Location, Vehicle


@dataclass(frozen=True)
class Route:
    origin: Location
    destination: Location
    distance_miles: float
    travel_minutes: float
    provider: str = "geodesic-estimate"


class RouteProvider(Protocol):
    name: str

    def route(self, origin: Location, destination: Location, vehicle: Vehicle | None = None) -> Route:
        ...


def haversine_miles(origin: Location, destination: Location) -> float:
    """Great-circle distance between coordinates in statute miles."""
    if origin.latitude is None or origin.longitude is None:
        raise ValueError("Origin coordinates are required for distance calculation")
    if destination.latitude is None or destination.longitude is None:
        raise ValueError("Destination coordinates are required for distance calculation")

    lat1, lon1, lat2, lon2 = map(
        radians, [origin.latitude, origin.longitude, destination.latitude, destination.longitude]
    )
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 3958.7613 * 2 * asin(sqrt(a))


@dataclass(frozen=True)
class SpeedModel:
    average_mph: float = 50.0
    road_factor: float = 1.0

    def travel_minutes(self, distance_miles: float) -> float:
        if self.average_mph <= 0:
            raise ValueError("average_mph must be positive")
        if self.road_factor <= 0:
            raise ValueError("road_factor must be positive")
        return distance_miles / (self.average_mph * self.road_factor) * 60


@dataclass(frozen=True)
class GeodesicRouteProvider:
    speed_model: SpeedModel = SpeedModel()
    name: str = "geodesic-estimate"

    def route(self, origin: Location, destination: Location, vehicle: Vehicle | None = None) -> Route:
        distance = haversine_miles(origin, destination)
        return Route(origin, destination, distance, self.speed_model.travel_minutes(distance), self.name)


def deadhead_miles(current: Location | None, pickup: Location, provider: RouteProvider) -> float:
    """Empty miles required to reach the pickup point."""
    if current is None:
        return 0.0
    return provider.route(current, pickup).distance_miles


def route_miles(origin: Location, destination: Location, provider: RouteProvider) -> float:
    return provider.route(origin, destination).distance_miles
