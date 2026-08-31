# Shark Logistics Engine

Modular logistics operating and decision engine designed to start with a single box truck and scale to a multi-vehicle fleet.

## Current phase

**Build 01 — Core Foundation**

The repository currently establishes the architecture, agent rules, audit specification, and foundational domain schemas for shipments, locations, time windows, vehicles, and customers.

## Core principle

The engine is provider-independent. Routing, tracking, traffic, and other external services will be connected through adapters rather than embedded into core business logic.

## Decision pipeline

```text
request -> normalize -> enrich -> calculate -> validate -> score -> audit -> approve/reject -> record
```

Agents propose decisions. Deterministic validation and audit logic controls whether those decisions can proceed.

## Planned capabilities

- shipment intake
- routing and distance
- fleet management
- dispatch optimization
- driver scheduling
- fuel and operating economics
- customer/load management
- shipment tracking
- lane profitability
- fleet scaling simulation
- operations dashboard

See `docs/ARCHITECTURE.md` and `docs/BUILD_PLAN.md` for the system design and build sequence.
