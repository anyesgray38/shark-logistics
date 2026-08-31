# Logistics Audit Agent

## Purpose

Catch invalid, contradictory, incomplete, or unsafe logistics decisions before they are accepted by the engine.

## Required checks

### Shipment
- required origin exists
- required destination exists
- pickup and delivery windows are valid
- weight is non-negative
- dimensions are valid
- status transition is legal

### Vehicle
- vehicle is available
- capacity is sufficient
- vehicle status permits dispatch
- operating constraints are satisfied

### Route
- origin and destination are resolvable
- distance is non-negative
- estimated duration is plausible
- route data has provenance

### Economics
- revenue is non-negative
- cost components are non-negative
- profit calculation reconciles
- per-mile and per-hour metrics are mathematically valid

## Audit output

Every audit returns:

```json
{
  "passed": true,
  "severity": "info|warning|error|critical",
  "checks": [],
  "errors": [],
  "warnings": [],
  "provenance": [],
  "timestamp": ""
}
```

An error or critical finding blocks approval.
