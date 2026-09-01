import pytest

from logistics.models import Location, Vehicle
from logistics.routing import GeodesicRouteProvider, SpeedModel, deadhead_miles, haversine_miles


def atlanta() -> Location:
    return Location("Atlanta", "Atlanta", "GA", "30303", latitude=33.749, longitude=-84.388)


def thomaston() -> Location:
    return Location("Thomaston", "Thomaston", "GA", "30286", latitude=32.888, longitude=-84.327)


def test_haversine_distance_is_reasonable():
    distance = haversine_miles(thomaston(), atlanta())
    assert 50 < distance < 80


def test_route_returns_distance_and_time():
    provider = GeodesicRouteProvider(SpeedModel(average_mph=50))
    route = provider.route(thomaston(), atlanta())
    assert route.distance_miles > 0
    assert route.travel_minutes > 0
    assert route.provider == "geodesic-estimate"


def test_deadhead_is_zero_without_current_location():
    provider = GeodesicRouteProvider()
    assert deadhead_miles(None, thomaston(), provider) == 0


def test_deadhead_uses_current_location():
    provider = GeodesicRouteProvider()
    assert deadhead_miles(atlanta(), thomaston(), provider) > 0


def test_speed_model_rejects_invalid_values():
    with pytest.raises(ValueError):
        SpeedModel(average_mph=0).travel_minutes(10)
    with pytest.raises(ValueError):
        SpeedModel(road_factor=0).travel_minutes(10)


def test_distance_requires_coordinates():
    missing = Location("Unknown", "Unknown", "GA", "00000")
    with pytest.raises(ValueError):
        haversine_miles(missing, atlanta())


def test_vehicle_can_be_passed_to_provider_without_changing_contract():
    provider = GeodesicRouteProvider()
    vehicle = Vehicle("TRUCK-001", "26ft_box_truck", 10000)
    route = provider.route(thomaston(), atlanta(), vehicle)
    assert route.distance_miles > 0
