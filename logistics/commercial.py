"""Deterministic commercial intelligence for Build 06."""

from dataclasses import dataclass
import math
from statistics import mean
from typing import Iterable

from .economics import CostInputs, load_economics
from .models import Shipment
from .routing import RouteProvider


@dataclass(frozen=True)
class LoadQuote:
    shipment_id: str
    offered_rate: float
    estimated_cost: float
    estimated_profit: float
    margin: float
    loaded_miles: float
    deadhead_miles: float
    total_miles: float
    revenue_per_mile: float
    profit_per_mile: float


@dataclass(frozen=True)
class CustomerScore:
    customer_id: str
    loads: int
    average_revenue: float
    average_margin: float
    score: float


@dataclass(frozen=True)
class LaneRateAnalysis:
    origin: str
    destination: str
    observations: int
    average_rate: float
    min_rate: float
    max_rate: float
    average_rate_per_mile: float


@dataclass(frozen=True)
class OpportunityScore:
    shipment_id: str
    score: float
    decision: str
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class CommercialAudit:
    passed: bool
    checks: tuple[str, ...]
    errors: tuple[str, ...]


def quote_load(shipment: Shipment, route_provider: RouteProvider, cost_inputs: CostInputs, offered_rate: float | None = None, deadhead_miles: float = 0.0, fixed_cost_allocation: float = 0.0) -> LoadQuote:
    """Calculate transparent economics for a single shipment opportunity."""
    rate = shipment.revenue if offered_rate is None else offered_rate
    if rate < 0 or deadhead_miles < 0:
        raise ValueError("rate and deadhead_miles cannot be negative")
    route = route_provider.route(shipment.pickup, shipment.delivery)
    if route.distance_miles < 0 or route.travel_minutes < 0:
        raise ValueError("route metrics cannot be negative")
    economics = load_economics(rate, route.distance_miles, deadhead_miles, route.travel_minutes / 60.0, cost_inputs, fixed_cost_allocation)
    total = economics.loaded_miles + economics.deadhead_miles
    return LoadQuote(shipment.shipment_id, rate, economics.total_cost, economics.gross_profit, economics.profit_margin, economics.loaded_miles, economics.deadhead_miles, total, rate / total if total else 0.0, economics.gross_profit / total if total else 0.0)


def score_customer(customer_id: str, quotes: Iterable[LoadQuote]) -> CustomerScore:
    items = tuple(quotes)
    if not customer_id.strip():
        raise ValueError("customer_id is required")
    if not items:
        return CustomerScore(customer_id, 0, 0.0, 0.0, 0.0)
    avg_revenue = mean(q.offered_rate for q in items)
    avg_margin = mean(q.margin for q in items)
    score = max(0.0, min(100.0, avg_margin * 70.0 + min(avg_revenue / 100.0, 30.0)))
    return CustomerScore(customer_id, len(items), avg_revenue, avg_margin, score)


def analyze_lane(origin: str, destination: str, rates: Iterable[tuple[float, float]]) -> LaneRateAnalysis:
    """Summarize observed lane rates as (rate, miles) pairs."""
    observations = tuple(rates)
    if not origin.strip() or not destination.strip() or not observations:
        raise ValueError("lane endpoints and observations are required")
    for rate, miles in observations:
        if rate < 0 or miles <= 0:
            raise ValueError("rate must be non-negative and miles must be positive")
    values = [rate for rate, _ in observations]
    return LaneRateAnalysis(origin, destination, len(values), mean(values), min(values), max(values), mean(rate / miles for rate, miles in observations))


def rank_opportunity(quote: LoadQuote, minimum_margin: float = 0.15) -> OpportunityScore:
    """Rank an opportunity using deterministic economics only."""
    if not 0.0 <= minimum_margin <= 1.0:
        raise ValueError("minimum_margin must be between 0 and 1")
    reasons: list[str] = []
    score = 0.0
    if quote.margin >= minimum_margin:
        score += 60.0; reasons.append("MARGIN_TARGET_MET")
    else:
        reasons.append("MARGIN_TARGET_MISSED")
    if quote.profit_per_mile > 0:
        score += min(25.0, quote.profit_per_mile); reasons.append("POSITIVE_PROFIT_PER_MILE")
    else:
        reasons.append("NON_POSITIVE_PROFIT_PER_MILE")
    if quote.revenue_per_mile >= 2.0:
        score += 15.0; reasons.append("RATE_PER_MILE_TARGET_MET")
    decision = "accept" if score >= 75.0 and quote.estimated_profit > 0 else "review" if quote.estimated_profit > 0 else "reject"
    return OpportunityScore(quote.shipment_id, min(100.0, score), decision, tuple(reasons))


def audit_opportunity(quote: LoadQuote, ranking: OpportunityScore) -> CommercialAudit:
    checks = ["IDENTITY_MATCHED", "NUMERIC_VALUES_FINITE", "PROFIT_RECONCILES", "SCORE_BOUNDED"]
    errors: list[str] = []
    if quote.shipment_id != ranking.shipment_id:
        errors.append("SHIPMENT_ID_MISMATCH")
    for name, value in (("offered_rate", quote.offered_rate), ("estimated_cost", quote.estimated_cost), ("estimated_profit", quote.estimated_profit), ("margin", quote.margin), ("score", ranking.score)):
        if not math.isfinite(value):
            errors.append(f"NON_FINITE_{name.upper()}")
    if abs((quote.offered_rate - quote.estimated_cost) - quote.estimated_profit) > 1e-9:
        errors.append("PROFIT_RECONCILIATION_FAILED")
    if not 0.0 <= ranking.score <= 100.0:
        errors.append("SCORE_OUT_OF_RANGE")
    return CommercialAudit(not errors, tuple(checks), tuple(errors))
