from datetime import datetime, timezone

from logistics.audit import AuditEvent
from logistics.intake import intake_shipment, shipment_fingerprint
from logistics.models import Location, Shipment, ShipmentStatus, TimeWindow

UTC = timezone.utc


def make_shipment(shipment_id="S-001"):
    return Shipment(
        shipment_id=shipment_id,
        customer_id="C-001",
        pickup=Location("1 Main St", "Thomaston", "GA", "30286"),
        delivery=Location("100 Peachtree St", "Atlanta", "GA", "30303"),
        pickup_window=TimeWindow(
            datetime(2026, 9, 1, 8, tzinfo=UTC),
            datetime(2026, 9, 1, 10, tzinfo=UTC),
        ),
        weight_lbs=500,
        revenue=750,
        status=ShipmentStatus.DRAFT,
        notes=["  fragile  ", "", "  "],
    )


def test_intake_normalizes_and_accepts():
    result = intake_shipment(make_shipment(" S-001 "))
    assert result.accepted
    assert result.shipment.shipment_id == "S-001"
    assert result.shipment.notes == ["fragile"]
    assert result.audit_event.outcome == "accepted"


def test_duplicate_is_rejected():
    original = make_shipment()
    result = intake_shipment(make_shipment("S-002"), existing=[original])
    assert not result.accepted
    assert "DUPLICATE_SHIPMENT" in {issue.code for issue in result.validation.issues}
    assert result.audit_event.outcome == "rejected"


def test_audit_event_is_immutable():
    event = AuditEvent.create("E-1", "test", "S-1", "accepted")
    try:
        event.outcome = "rejected"
    except Exception:
        pass
    else:
        raise AssertionError("AuditEvent must be immutable")


def test_fingerprint_ignores_shipment_id():
    assert shipment_fingerprint(make_shipment("S-001")) == shipment_fingerprint(make_shipment("S-999"))
