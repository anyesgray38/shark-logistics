# Shark Logistics Engine Architecture

## Mission

Build a modular logistics operating and decision engine that can start with one box truck and scale to a multi-vehicle fleet.

## Design principles

1. Core logic must work without external APIs.
2. External providers are adapters, never core dependencies.
3. Every operational decision must be auditable.
4. Agents propose; deterministic validators approve or reject.
5. All calculations must be reproducible from recorded inputs.
6. Simulation comes before automation of real-world operations.

## Layers

```text
Inputs
  -> Domain Models
  -> Deterministic Engine
  -> Agent Orchestration
  -> Validation / Audit
  -> Decision
  -> Provider Adapters
  -> Operational Output
```

## Planned domains

- shipments
- customers
- vehicles
- drivers
- locations
- routes
- dispatch
- pricing
- fuel and operating costs
- maintenance
- tracking
- fleet analytics

## Provider adapter targets

Initial candidates:

- OpenStreetMap / Nominatim
- openrouteservice
- TomTom
- Road511
- shipment tracking providers

No provider is required for the core simulation or validation layer.
