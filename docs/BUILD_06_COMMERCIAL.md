# Build 06 — Commercial Intelligence

## Purpose

Turn a shipment opportunity into a transparent commercial decision without allowing an agent or external provider to bypass deterministic economics.

## Pipeline

```text
LOAD INTAKE
   ↓
ROUTE ESTIMATE
   ↓
COST MODEL
   ↓
LOAD QUOTE
   ↓
LANE / CUSTOMER ANALYSIS
   ↓
OPPORTUNITY SCORE
   ↓
INDEPENDENT COMMERCIAL AUDIT
   ↓
ACCEPT / REVIEW / REJECT
```

## Components

- `quote_load`: combines route distance and Build 03 economics.
- `score_customer`: summarizes observed customer revenue and margins.
- `analyze_lane`: summarizes supplied rate observations and rate-per-mile.
- `rank_opportunity`: deterministic opportunity ranking.
- `audit_opportunity`: independent reconciliation and numeric safety gate.

## Safety boundary

Commercial intelligence does not invent market rates. Rate observations are explicit inputs. Future research/provider agents may supply evidence, but deterministic logic verifies calculations before a commercial decision is trusted.

## Decision policy

- `accept`: score ≥ 75 and positive estimated profit.
- `review`: positive estimated profit but score below acceptance threshold.
- `reject`: non-positive estimated profit.

The policy is intentionally simple and replaceable. Build 06 establishes the decision interface; later builds can add historical lane distributions, customer reliability, capacity scarcity, and market evidence without changing the core audit boundary.
