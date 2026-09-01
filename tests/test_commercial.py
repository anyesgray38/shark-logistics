from datetime import datetime, timedelta, timezone

import pytest

from logistics.commercial import analyze_lane, audit_opportunity, quote_load, rank_opportunity, score_customer
from logistics.economics import CostInputs
from logistics.models import Location, Shipment, TimeWindow
from logistics.routing import GeodesicRouteProvider


def loc(name, lat, lon):
    return Location(name, name, "GA", "00000", latitude=lat, longitude=lon)


def load(revenue=1000):
    now = datetime(2026, 9, 1, 8, tzinfo=timezone.utc)
    return Shipment("S1", "C1", loc("A", 33.75, -84.39), loc("B", 33.80, -84.40), TimeWindow(now, now + timedelta(hours=4)), revenue=revenue)


def costs():
    return CostInputs(fuel_price_per_gallon=3.50, fuel_economy_mpg=10, driver_cost_per_hour=25, maintenance_per_mile=.20)


def test_quote_reconciles_profit():
    q = quote_load(load(1000), GeodesicRouteProvider(), costs())
    assert q.estimated_profit == pytest.approx(q.offered_rate - q.estimated_cost)
    assert q.total_miles == pytest.approx(q.loaded_miles + q.deadhead_miles)


def test_deadhead_changes_cost():
    provider = GeodesicRouteProvider()
    a = quote_load(load(), provider, costs(), deadhead_miles=0)
    b = quote_load(load(), provider, costs(), deadhead_miles=20)
    assert b.estimated_cost > a.estimated_cost


def test_lane_analysis_is_deterministic():
    result = analyze_lane("Atlanta", "Macon", [(500, 100), (600, 120)])
    assert result.observations == 2
    assert result.average_rate == pytest.approx(550)
    assert result.average_rate_per_mile == pytest.approx(5)


def test_customer_score_uses_observed_quotes():
    provider = GeodesicRouteProvider()
    quotes = [quote_load(load(1000), provider, costs()), quote_load(load(1200), provider, costs())]
    result = score_customer("C1", quotes)
    assert result.loads == 2
    assert 0 <= result.score <= 100


def test_opportunity_accepts_strong_positive_load():
    q = quote_load(load(5000), GeodesicRouteProvider(), costs())
    ranking = rank_opportunity(q)
    audit = audit_opportunity(q, ranking)
    assert ranking.decision == "accept"
    assert audit.passed


def test_negative_profit_is_rejected():
    q = quote_load(load(0), GeodesicRouteProvider(), costs())
    assert q.estimated_profit < 0
    ranking = rank_opportunity(q)
    assert ranking.decision == "reject"


def test_audit_catches_identity_mismatch():
    q = quote_load(load(), GeodesicRouteProvider(), costs())
    ranking = rank_opportunity(q)
    bad = ranking.__class__("OTHER", ranking.score, ranking.decision, ranking.reasons)
    audit = audit_opportunity(q, bad)
    assert not audit.passed
    assert "SHIPMENT_ID_MISMATCH" in audit.errors
