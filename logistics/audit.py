"""Immutable audit events for every deterministic decision."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    event_type: str
    subject_id: str
    timestamp: datetime
    outcome: str
    details: dict[str, Any]

    @classmethod
    def create(
        cls,
        event_id: str,
        event_type: str,
        subject_id: str,
        outcome: str,
        details: dict[str, Any] | None = None,
    ) -> "AuditEvent":
        return cls(
            event_id=event_id,
            event_type=event_type,
            subject_id=subject_id,
            timestamp=datetime.now(timezone.utc),
            outcome=outcome,
            details=dict(details or {}),
        )
