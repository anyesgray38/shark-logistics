from datetime import datetime, timezone

from logistics.models import Location, Shipment, TimeWindow, Vehicle
from logistics.validation import validate_shipment, validate_vehicle


UTC = timezone.utc


def location(city: str) -> Location:
    return Location("1 Main St", city, "GA", "30286")


def test_valid_shipment_passes():
    shipment = Shipment(
        shipment_id="S-001",
        customer_id="C-001",
        pickup=location("Thomaston"),
        delivery=location("Atlanta"),
        pickup_window=TimeWindow(
            datetime(2026, 9, 1, 8, tzinfo=UTC),
            datetime(2026, 9, 1, 10, tzinfo=UTC),
        ),
        weight_lbs=500,
        revenue=750,
    )
    assert validate_shipment(shipment).valid


def test_invalid_shipment_reports_multiple_issues():
    shipment = Shipment(
        shipment_id="",
        customer_id="",
        pickup=location("Thomaston"),
        delivery=location("Atlanta"),
        pickup_window=TimeWindow(
            datetime(2026, 9, 1, 10, tzinfo=UTC),
            datetime(2026, 9, 1, 8, tzinfo=UTC),
        ),
        weight_lbs=-1,
        revenue=-5,
    )
    result = validate_shipment(shipment)
    assert not result.valid
    assert {issue.code for issue in result.issues} >= {
        "SHIPMENT_ID_REQUIRED",
        "CUSTOMER_ID_REQUIRED",
        "NEGATIVE_WEIGHT",
        "NEGATIVE_REVENUE",
        "INVALID_PICKUP_WINDOW",
    }


def test_valid_vehicle_passes():
    vehicle = Vehicle(
        vehicle_id="TRUCK-001",
        vehicle_type="26ft_box_truck",
        max_weight_lbs=10000,
        max_volume_cuft=1700,
        fuel_economy_mpg=10,
    )
    assert validate_vehicle(vehicle).valid


def test_invalid_vehicle_fails():
    vehicle = Vehicle(
        vehicle_id="TRUCK-001",
        vehicle_type="26ft_box_truck",
        max_weight_lbs=0,
        fuel_economy_mpg=-1,
    )
    result = validate_vehicle(vehicle)
    assert not result.valid
    assert {issue.code for issue in result.issues} >= {
        "INVALID_WEIGHT_CAPACITY",
        "INVALID_FUEL_ECONOMY",
    }
