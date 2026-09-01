"""Shipment intake, normalization, and deterministic duplicate detection."""

from dataclasses import dataclass
from typing import Any

from .audit import AuditEvent
from .models import Shipment
from .validation import ValidationResult, validate_shipment


@dataclass(frozen=True)
class IntakeResult:
    accepted: bool
    shipment: Shipment | None
    validation: ValidationResult
    audit_event: AuditEvent


def normalize_text(value: str | None) -> str:
    return " ".join((value or "").strip().split())


def shipment_fingerprint(shipment: Shipment) -> tuple[Any, ...]:
    """Stable business-key fingerprint; deliberately excludes mutable status."""
    return (
        shipment.customer_id.strip().lower(),
        shipment.pickup.address.strip().lower(),
        shipment.pickup.city.strip().lower(),
        shipment.pickup.state.strip().upper(),
        shipment.delivery.address.strip().lower(),
        shipment.delivery.city.strip().lower(),
        shipment.delivery.state.strip().upper(),
        shipment.pickup_window.start,
        shipment.pickup_window.end,
        shipment.weight_lbs,
        shipment.volume_cuft,
        shipment.revenue,
    )


def intake_shipment(shipment: Shipment, existing: list[Shipment] | None = None) -> IntakeResult:
    existing = existing or []
    normalized = Shipment(
        shipment_id=normalize_text(shipment.shipment_id),
        customer_id=normalize_text(shipment.customer_id),
        pickup=shipment.pickup,
        delivery=shipment.delivery,
        pickup_window=shipment.pickup_window,
        delivery_window=shipment.delivery_window,
        weight_lbs=shipment.weight_lbs,
        volume_cuft=shipment.volume_cuft,
        revenue=shipment.revenue,
        status=shipment.status,
        notes=[normalize_text(note) for note in shipment.notes if normalize_text(note)],
    )

    result = validate_shipment(normalized)
    duplicate = any(shipment_fingerprint(item) == shipment_fingerprint(normalized) for item in existing)
    if duplicate:
        from .validation import ValidationIssue
        result = ValidationResult.from_issues(
            [*result.issues, ValidationIssue("DUPLICATE_SHIPMENT", "Shipment matches an existing shipment.", "shipment")]
        )

    accepted = result.valid
    event = AuditEvent.create(
        event_id=f"intake:{normalized.shipment_id or 'unknown'}",
        event_type="shipment_intake",
        subject_id=normalized.shipment_id or "unknown",
        outcome="accepted" if accepted else "rejected",
        details={"issue_codes": [issue.code for issue in result.issues]},
    )
    return IntakeResult(accepted, normalized if accepted else None, result, event)
