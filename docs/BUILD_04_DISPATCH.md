# Build 04 — Dispatch Engine

Build 04 turns routing and economics into deterministic dispatch decisions.

## Pipeline

```text
shipment + fleet
      ↓
capacity/status validation
      ↓
route feasibility
      ↓
pickup window
      ↓
delivery window
      ↓
economic scoring
      ↓
independent audit gate
      ↓
best vehicle / multi-stop plan
```

## Components

### Feasibility
Checks:
- vehicle availability
- shipment dispatchability
- weight capacity
- volume capacity when both values exist
- route resolvability
- pickup time window
- delivery time window

### Scoring
Candidate assignments are scored from deterministic signals:
- estimated profit
- deadhead efficiency
- pickup urgency
- vehicle utilization

### Multi-stop planning
The current planner greedily selects the highest-scoring feasible shipment, executes its pickup/delivery pair, updates the vehicle's location/time, and repeats. This is intentionally deterministic and forms the baseline that a future VROOM/PyVRP optimization adapter can replace or benchmark.

### Audit gate
Every proposed candidate is independently checked before assignment. Infeasible candidates, negative distances/times, non-finite scores, and failed profit reconciliation are blocked.

## Safety boundary

Build 04 remains a planning/simulation engine. It does not control vehicles or create binding freight commitments. Human approval and validated operational integrations remain required for real-world execution.
