# Build 03 — Fleet Economics

Build 03 establishes deterministic unit economics for loads and vehicles.

## Calculation flow

```text
load revenue
    ↓
loaded miles + deadhead miles
    ↓
fuel consumption
    ↓
driver hours
    ↓
maintenance
    ↓
allocated fixed costs
    ↓
total operating cost
    ↓
gross/operating profit
    ↓
margin + cost per mile
```

## Design rules

1. Fuel, driver, maintenance, and fixed costs are calculated deterministically.
2. Deadhead miles are included in variable operating cost.
3. Load economics and fleet economics remain separate models.
4. Agents may propose rates, assignments, or forecasts, but deterministic economics validates the arithmetic.
5. Provider-specific pricing data belongs behind adapters.
6. No autonomous binding freight commitment is allowed by this layer.

## Next build

Build 04 adds dispatch feasibility and scoring on top of the routing and economics layers.
