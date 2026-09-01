from datetime import datetime, timedelta, timezone

import pytest

from logistics.dispatch import DispatchConfig, assign_best_vehicle, check_feasibility, plan_multi_stop
from logistics.models import Location, Shipment, TimeWindow, Vehicle, VehicleStatus
from logistics.routing import GeodesicRouteProvider, SpeedModel


def location(name: str, lat: float, lon: float) -> Location:
    return Location(name, name, "GA", "00000", latitude=lat, longitude=lon)


def shipment(shipment_id="S1", weight=1000, revenue=1000) -> Shipment:
    now = datetime(2026, 9, 1, 8, tzinfo=timezone.utc)
    return Shipment(
        shipment_id=shipment_id,
        customer_id="C1",
        pickup=location("Pickup", 33.75, -84.39),
        delivery=location("Delivery", 33.80, -84.40),
        pickup_window=TimeWindow(now, now + timedelta(hours=4)),
        delivery_window=TimeWindow(now, now + timedelta(hours=8)),
        weight_lbs=weight,
        revenue=revenue,
    )


def truck(weight=10000, status=VehicleStatus.AVAILABLE) -> Vehicle:
    return Vehicle(
        "TRUCK-001",
        "26ft_box_truck",
        weight,
        status=status,
        current_location=location("Depot", 33.70, -84.30),
    )


def test_capacity_is_a_hard_constraint():
    provider = GeodesicRouteProvider(SpeedModel(average_mph=50))
    result = check_feasibility(
        truck(weight=500),
        shipment(weight=1000),
        datetime(2026, 9, 1, 8, tzinfo=timezone.utc),
        provider,
    )
    assert not result.feasible
    assert "WEIGHT_CAPACITY_EXCEEDED" in result.reasons


def test_unavailable_vehicle_is_rejected():
    provider = GeodesicRouteProvider()
    result = check_feasibility(
        truck(status=VehicleStatus.MAINTENANCE),
        shipment(),
        datetime(2026, 9, 1, 8, tzinfo=timezone.utc),
        provider,
    )
    assert not result.feasible
    assert "VEHICLE_NOT_AVAILABLE" in result.reasons


def test_best_vehicle_assignment_prefers_lower_deadhead():
    provider = GeodesicRouteProvider(SpeedModel(average_mph=50))
    start = datetime(2026, 9, 1, 8, tzinfo=timezone.utc)
    near = truck()
    near.vehicle_id = "A"
    near.current_location = location("Near", 33.74, -84.38)
    far = truck()
    far.vehicle_id = "B"
    far.current_location = location("Far", 34.20, -84.80)
    result = assign_best_vehicle(shipment(), [far, near], start, provider)
    assert result is not None
    assert result.vehicle.vehicle_id == "A"


def test_time_window_miss_blocks_dispatch():
    provider = GeodesicRouteProvider(SpeedModel(average_mph=20))
    s = shipment()
    s.pickup_window = TimeWindow(
        datetime(2026, 9, 1, 8, tzinfo=timezone.utc),
        datetime(2026, 9, 1, 8, minute=1, tzinfo=timezone.utc),
    )
    result = check_feasibility(truck(), s, datetime(2026, 9, 1, 8, tzinfo=timezone.utc), provider)
    assert not result.feasible
    assert "PICKUP_WINDOW_MISSED" in result.reasons


def test_multi_stop_plan_is_deterministic_and_delivers_each_selected_load():
    provider = GeodesicRouteProvider(SpeedModel(average_mph=50))
    start = datetime(2026, 9, 1, 8, tzinfo=timezone.utc)
    plan = plan_multi_stop([shipment("S1", revenue=1000), shipment("S2", revenue=2000)], truck(), start, provider)
    assert [s.shipment_id for s in plan.shipments] == ["S2", "S1"]
    assert plan.total_miles > 0
    assert plan.estimated_revenue == pytest.approx(3000)
    assert len(plan.candidates) == 2


def test_dispatch_config_rejects_all_zero_weights():
    with pytest.raises(ValueError):
        DispatchConfig(0, 0, 0, 0, 0).validate()
