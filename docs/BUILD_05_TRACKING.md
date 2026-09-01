# Build 05 — Tracking Engine

Build 05 adds a provider-independent shipment tracking state machine. Tracking is modeled as an immutable event stream reduced into a deterministic current snapshot.

## Pipeline

```text
provider/internal event
        ↓
shipment identity validation
        ↓
chronological ordering
        ↓
legal lifecycle transition
        ↓
ETA validation
        ↓
deterministic reducer
        ↓
independent tracking audit gate
        ↓
current tracking snapshot
```

## Lifecycle

The shipment lifecycle is:

```text
draft → ready → assigned → in_transit → delivered
   └──────────────→ cancelled
```

Terminal states cannot regress. Repeated events for the current state are permitted for idempotent provider updates.

## Components

### TrackingEvent
Immutable event containing shipment ID, event ID, status, timestamp, optional location, source, and optional ETA.

### Reducer
`reduce_tracking` validates the complete event stream and produces a `TrackingSnapshot` without mutating the domain shipment.

### ETA
`EtaEstimate` keeps arrival time, source, and optional confidence separate from the shipment lifecycle so provider-specific ETA logic can be added later.

### Provider boundary
`TrackingProvider` defines the adapter contract. External tracking services can implement it without entering core business logic.

### Audit gate
`audit_tracking` independently checks shipment identity, event ordering, lifecycle transitions, ETA chronology, and ETA confidence.

## Safety boundary

Build 05 consumes tracking observations; it does not control vehicles, silently rewrite shipment state, or treat an external provider response as authoritative without deterministic validation.
