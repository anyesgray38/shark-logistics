# Build Plan

## Build 01 — Core foundation — COMPLETE

- domain schemas
- shipment intake model
- vehicle model
- customer model
- location model
- deterministic validators
- audit events
- test fixtures

## Build 02 — Routing — COMPLETE

- distance calculation
- route abstraction
- travel-time model
- route alternatives
- deadhead calculation
- provider adapter boundary
- routing tests

## Build 03 — Fleet economics — COMPLETE

- fuel model
- driver cost
- rental/lease allocation
- insurance allocation
- maintenance allocation
- cost per mile/hour/load
- load economics
- fleet economics
- deterministic economics tests

## Build 04 — Dispatch — COMPLETE

- vehicle assignment
- time-window constraints
- capacity constraints
- multi-stop planning
- dispatch scoring
- feasibility validation
- independent dispatch audit gate
- deterministic dispatch tests

## Build 05 — Tracking — COMPLETE

- shipment lifecycle
- immutable status events
- deterministic tracking reducer
- ETA abstraction
- provider adapter boundary
- independent tracking audit gate
- deterministic tracking tests

## Build 06 — Commercial intelligence — COMPLETE

- load economics quote layer
- customer scoring
- lane rate analysis
- opportunity ranking
- independent commercial audit gate
- deterministic commercial tests

## Build 07 — Fleet scaling — NEXT

- multi-vehicle simulation
- utilization
- fleet profitability
- replacement/addition decisions

## Build 08 — Operations dashboard

- fleet state
- active shipments
- dispatch board
- profitability
- exceptions
- audit history

## Build 09 — Agent operating layer

- orchestrator runtime
- planner
- researcher
- analyst
- executor
- auditor
- evidence ledger
- workflow state
- permission gates

## Build 10 — Customer platform

- customer onboarding
- shipment quote request
- booking workflow
- customer tracking
- document center
- notifications
- account portal
