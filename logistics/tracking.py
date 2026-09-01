"""Deterministic shipment tracking state, ETA, and provider boundaries for Build 05."""

from dataclasses import dataclass
from datetime import datetime
import math
from typing import Protocol

from .models import Location, Shipment, ShipmentStatus


_ALLOWED_TRANSITIONS: dict[ShipmentStatus, frozenset[ShipmentStatus]] = {
    ShipmentStatus.DRAFT: frozenset({ShipmentStatus.DRAFT, ShipmentStatus.READY, ShipmentStatus.CANCELLED}),
    ShipmentStatus.READY: frozenset({ShipmentStatus.READY, ShipmentStatus.ASSIGNED, ShipmentStatus.CANCELLED}),
    ShipmentStatus.ASSIGNED: frozenset({ShipmentStatus.ASSIGNED, ShipmentStatus.IN_TRANSIT, ShipmentStatus.CANCELLED}),
    ShipmentStatus.IN_TRANSIT: frozenset({ShipmentStatus.IN_TRANSIT, ShipmentStatus.DELIVERED}),
    ShipmentStatus.DELIVERED: frozenset({ShipmentStatus.DELIVERED}),
    ShipmentStatus.CANCELLED: frozenset({ShipmentStatus.CANCELLED}),
}


@dataclass(frozen=True)
class EtaEstimate:
    estimated_arrival: datetime
    source: str = "deterministic"
    confidence: float | None = None


@dataclass(frozen=True)
class TrackingEvent:
    event_id: str
    shipment_id: str
    status: ShipmentStatus
    occurred_at: datetime
    location: Location | None = None
    source: str = "internal"
    eta: EtaEstimate | None = None


@dataclass(frozen=True)
class TrackingSnapshot:
    shipment_id: str
    status: ShipmentStatus
    latest_event: TrackingEvent | None
    current_location: Location | None
    eta: EtaEstimate | None
    event_count: int


class TrackingProvider(Protocol):
    """Adapter contract for external tracking providers."""

    name: str

    def fetch_events(self, shipment_id: str) -> tuple[TrackingEvent, ...]:
        ...


def legal_transitions(status: ShipmentStatus) -> frozenset[ShipmentStatus]:
    return _ALLOWED_TRANSITIONS[status]


def reduce_tracking(shipment: Shipment, events: list[TrackingEvent] | tuple[TrackingEvent, ...]) -> TrackingSnapshot:
    """Apply an ordered event stream without mutating the shipment."""
    current = shipment.status
    previous_time: datetime | None = None
    seen_ids: set[str] = set()
    latest: TrackingEvent | None = None
    current_location: Location | None = None
    eta: EtaEstimate | None = None

    for event in events:
        if event.shipment_id != shipment.shipment_id:
            raise ValueError("TRACKING_SHIPMENT_MISMATCH")
        if not event.event_id.strip():
            raise ValueError("TRACKING_EVENT_ID_REQUIRED")
        if event.event_id in seen_ids:
            raise ValueError("DUPLICATE_TRACKING_EVENT")
        if previous_time is not None and event.occurred_at < previous_time:
            raise ValueError("OUT_OF_ORDER_TRACKING_EVENT")
        if event.status not in legal_transitions(current):
            raise ValueError(f"ILLEGAL_STATUS_TRANSITION:{current.value}->{event.status.value}")
        if event.occurred_at.tzinfo is None:
            raise ValueError("TRACKING_TIMESTAMP_MUST_BE_TIMEZONE_AWARE")
        if event.eta is not None:
            if event.eta.estimated_arrival.tzinfo is None:
                raise ValueError("ETA_TIMESTAMP_MUST_BE_TIMEZONE_AWARE")
            if event.eta.confidence is not None and not 0.0 <= event.eta.confidence <= 1.0:
                raise ValueError("ETA_CONFIDENCE_OUT_OF_RANGE")
        seen_ids.add(event.event_id)
        previous_time = event.occurred_at
        current = event.status
        latest = event
        if event.location is not None:
            current_location = event.location
        if event.eta is not None:
            eta = event.eta

    return TrackingSnapshot(
        shipment_id=shipment.shipment_id,
        status=current,
        latest_event=latest,
        current_location=current_location,
        eta=eta,
        event_count=len(events),
    )


def audit_tracking(shipment: Shipment, events: list[TrackingEvent] | tuple[TrackingEvent, ...]) -> TrackingAudit:
    """Independent deterministic gate for a tracking event stream."""
    checks: list[str] = []
    errors: list[str] = []
    try:
        snapshot = reduce_tracking(shipment, events)
        checks.extend(("SHIPMENT_MATCHED", "EVENT_ORDER_VALID", "STATUS_TRANSITIONS_VALID"))
        if snapshot.eta is not None and snapshot.eta.estimated_arrival < snapshot.latest_event.occurred_at:
            errors.append("ETA_BEFORE_LATEST_EVENT")
        if snapshot.eta is not None and snapshot.eta.confidence is not None and not math.isfinite(snapshot.eta.confidence):
            errors.append("NON_FINITE_ETA_CONFIDENCE")
    except ValueError as exc:
        errors.append(str(exc))
    return TrackingAudit(not errors, tuple(checks), tuple(errors))


@dataclass(frozen=True)
class TrackingAudit:
    passed: bool
    checks: tuple[str, ...]
    errors: tuple[str, ...]
