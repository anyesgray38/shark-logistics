"""Provider-independent domain models for Build 01."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class VehicleStatus(str, Enum):
    AVAILABLE = "available"
    ASSIGNED = "assigned"
    IN_TRANSIT = "in_transit"
    MAINTENANCE = "maintenance"
    OUT_OF_SERVICE = "out_of_service"


class ShipmentStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    ASSIGNED = "assigned"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class Location:
    address: str
    city: str
    state: str
    postal_code: str
    country: str = "US"
    latitude: Optional[float] = None
    longitude: Optional[float] = None


@dataclass(frozen=True)
class TimeWindow:
    start: datetime
    end: datetime


@dataclass
class Customer:
    customer_id: str
    name: str
    contact_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


@dataclass
class Vehicle:
    vehicle_id: str
    vehicle_type: str
    max_weight_lbs: float
    max_volume_cuft: Optional[float] = None
    status: VehicleStatus = VehicleStatus.AVAILABLE
    current_location: Optional[Location] = None
    fuel_economy_mpg: Optional[float] = None
    operating_cost_per_mile: Optional[float] = None


@dataclass
class Shipment:
    shipment_id: str
    customer_id: str
    pickup: Location
    delivery: Location
    pickup_window: TimeWindow
    delivery_window: Optional[TimeWindow] = None
    weight_lbs: float = 0.0
    volume_cuft: Optional[float] = None
    revenue: float = 0.0
    status: ShipmentStatus = ShipmentStatus.DRAFT
    notes: list[str] = field(default_factory=list)
