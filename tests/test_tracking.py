from datetime import datetime, timedelta, timezone

import pytest

from logistics.models import Location, Shipment, ShipmentStatus, TimeWindow
from logistics.tracking import EtaEstimate, TrackingEvent, audit_tracking, reduce_tracking


def location(name: str = "Point") -> Location:
    return Location(name, "Atlanta", "GA", "30301", latitude=33.75, longitude=-84.39)


def shipment(status=ShipmentStatus.DRAFT) -> Shipment:
    start = datetime(2026, 9, 1, 8, tzinfo=timezone.utc)
    return Shipment(
        "S1", "C1", location("Pickup"), location("Delivery"),
        TimeWindow(start, start + timedelta(hours=4)),
        status=status,
    )


def event(event_id, status, minutes, eta=None):
    return TrackingEvent(
        event_id, "S1", status,
        datetime(2026, 9, 1, 8, tzinfo=timezone.utc) + timedelta(minutes=minutes),
        location(f"P{minutes}"), "test", eta,
    )


def test_lifecycle_reduces_to_latest_state_and_eta():
    eta = EtaEstimate(datetime(2026, 9, 1, 12, tzinfo=timezone.utc), confidence=0.9)
    events = [
        event("E1", ShipmentStatus.READY, 5),
        event("E2", ShipmentStatus.ASSIGNED, 10),
        event("E3", ShipmentStatus.IN_TRANSIT, 30, eta),
        event("E4", ShipmentStatus.DELIVERED, 120),
    ]
    snapshot = reduce_tracking(shipment(), events)
    assert snapshot.status is ShipmentStatus.DELIVERED
    assert snapshot.event_count == 4
    assert snapshot.current_location == events[-1].location
    assert snapshot.eta == eta


def test_illegal_transition_is_blocked():
    with pytest.raises(ValueError, match="ILLEGAL_STATUS_TRANSITION"):
        reduce_tracking(shipment(), [event("E1", ShipmentStatus.DELIVERED, 5)])


def test_out_of_order_event_is_blocked():
    events = [event("E1", ShipmentStatus.READY, 10), event("E2", ShipmentStatus.ASSIGNED, 5)]
    with pytest.raises(ValueError, match="OUT_OF_ORDER_TRACKING_EVENT"):
        reduce_tracking(shipment(), events)


def test_duplicate_event_is_blocked():
    e = event("E1", ShipmentStatus.READY, 5)
    with pytest.raises(ValueError, match="DUPLICATE_TRACKING_EVENT"):
        reduce_tracking(shipment(), [e, e])


def test_audit_gate_rejects_eta_before_latest_event():
    eta = EtaEstimate(datetime(2026, 9, 1, 8, 20, tzinfo=timezone.utc), confidence=0.8)
    events = [event("E1", ShipmentStatus.READY, 5), event("E2", ShipmentStatus.ASSIGNED, 30, eta)]
    audit = audit_tracking(shipment(), events)
    assert not audit.passed
    assert "ETA_BEFORE_LATEST_EVENT" in audit.errors


def test_audit_gate_accepts_valid_stream():
    events = [
        event("E1", ShipmentStatus.READY, 5),
        event("E2", ShipmentStatus.ASSIGNED, 10),
        event("E3", ShipmentStatus.IN_TRANSIT, 30),
    ]
    audit = audit_tracking(shipment(), events)
    assert audit.passed
    assert not audit.errors
    assert "STATUS_TRANSITIONS_VALID" in audit.checks


def test_tracking_is_non_mutating():
    s = shipment()
    reduce_tracking(s, [event("E1", ShipmentStatus.READY, 5)])
    assert s.status is ShipmentStatus.DRAFT
