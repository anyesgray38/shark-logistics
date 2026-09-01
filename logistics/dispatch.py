"""Deterministic dispatch feasibility, scoring, and multi-stop planning."""

from dataclasses import dataclass
from datetime import datetime, timedelta
import math

from .economics import CostInputs, load_economics
from .models import Shipment, Vehicle, VehicleStatus
from .routing import RouteProvider
from .validation import validate_shipment, validate_vehicle


@dataclass(frozen=True)
class DispatchConfig:
    pickup_service_minutes: float = 15.0
    delivery_service_minutes: float = 15.0
    profit_weight: float = 0.55
    deadhead_weight: float = 0.20
    urgency_weight: float = 0.15
    utilization_weight: float = 0.10

    def validate(self) -> None:
        for name in (
            "pickup_service_minutes",
            "delivery_service_minutes",
            "profit_weight",
            "deadhead_weight",
            "urgency_weight",
            "utilization_weight",
        ):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} cannot be negative")
        if sum((self.profit_weight, self.deadhead_weight, self.urgency_weight, self.utilization_weight)) <= 0:
            raise ValueError("at least one scoring weight must be positive")


@dataclass(frozen=True)
class DispatchFeasibility:
    feasible: bool
    vehicle_id: str
    shipment_id: str
    reasons: tuple[str, ...]
    deadhead_miles: float = 0.0
    loaded_miles: float = 0.0
    travel_minutes: float = 0.0
    pickup_arrival: datetime | None = None
    delivery_arrival: datetime | None = None


@dataclass(frozen=True)
class DispatchCandidate:
    vehicle: Vehicle
    shipment: Shipment
    feasibility: DispatchFeasibility
    score: float
    estimated_profit: float


@dataclass(frozen=True)
class DispatchAudit:
    passed: bool
    checks: tuple[str, ...]
    errors: tuple[str, ...]


@dataclass(frozen=True)
class DispatchPlan:
    vehicle: Vehicle
    shipments: tuple[Shipment, ...]
    candidates: tuple[DispatchCandidate, ...]
    total_miles: float
    total_travel_minutes: float
    estimated_revenue: float
    estimated_profit: float


def _arrive_at_window(current: datetime, travel_minutes: float, window) -> datetime:
    arrival = current + timedelta(minutes=travel_minutes)
    return max(arrival, window.start)


def check_feasibility(
    vehicle: Vehicle,
    shipment: Shipment,
    dispatch_start: datetime,
    provider: RouteProvider,
    config: DispatchConfig | None = None,
) -> DispatchFeasibility:
    """Check capacity, status, route resolution, and both time windows."""
    config = config or DispatchConfig()
    config.validate()
    reasons: list[str] = []

    vehicle_result = validate_vehicle(vehicle)
    shipment_result = validate_shipment(shipment)
    reasons.extend(issue.code for issue in vehicle_result.issues)
    reasons.extend(issue.code for issue in shipment_result.issues)

    if vehicle.status is not VehicleStatus.AVAILABLE:
        reasons.append("VEHICLE_NOT_AVAILABLE")
    if shipment.status.value in {"cancelled", "delivered"}:
        reasons.append("SHIPMENT_NOT_DISPATCHABLE")
    if shipment.weight_lbs > vehicle.max_weight_lbs:
        reasons.append("WEIGHT_CAPACITY_EXCEEDED")
    if (
        shipment.volume_cuft is not None
        and vehicle.max_volume_cuft is not None
        and shipment.volume_cuft > vehicle.max_volume_cuft
    ):
        reasons.append("VOLUME_CAPACITY_EXCEEDED")

    if reasons:
        return DispatchFeasibility(False, vehicle.vehicle_id, shipment.shipment_id, tuple(reasons))

    try:
        deadhead = provider.route(vehicle.current_location, shipment.pickup, vehicle) if vehicle.current_location else None
        pickup_route = provider.route(shipment.pickup, shipment.delivery, vehicle)
    except (ValueError, TypeError) as exc:
        return DispatchFeasibility(
            False,
            vehicle.vehicle_id,
            shipment.shipment_id,
            ("ROUTE_UNRESOLVABLE", str(exc)),
        )

    deadhead_miles = deadhead.distance_miles if deadhead else 0.0
    deadhead_minutes = deadhead.travel_minutes if deadhead else 0.0
    pickup_arrival = _arrive_at_window(dispatch_start, deadhead_minutes, shipment.pickup_window)
    if pickup_arrival > shipment.pickup_window.end:
        reasons.append("PICKUP_WINDOW_MISSED")

    delivery_start = pickup_arrival + timedelta(minutes=config.pickup_service_minutes)
    delivery_arrival = _arrive_at_window(delivery_start, pickup_route.travel_minutes, shipment.delivery_window) if shipment.delivery_window else delivery_start + timedelta(minutes=pickup_route.travel_minutes)
    if shipment.delivery_window and delivery_arrival > shipment.delivery_window.end:
        reasons.append("DELIVERY_WINDOW_MISSED")

    return DispatchFeasibility(
        not reasons,
        vehicle.vehicle_id,
        shipment.shipment_id,
        tuple(reasons),
        deadhead_miles,
        pickup_route.distance_miles,
        deadhead_minutes + pickup_route.travel_minutes,
        pickup_arrival,
        delivery_arrival,
    )


def score_candidate(
    vehicle: Vehicle,
    shipment: Shipment,
    feasibility: DispatchFeasibility,
    dispatch_start: datetime,
    config: DispatchConfig | None = None,
    cost_inputs: CostInputs | None = None,
) -> DispatchCandidate:
    """Score a feasible assignment deterministically; infeasible candidates score -inf."""
    config = config or DispatchConfig()
    config.validate()
    if not feasibility.feasible:
        return DispatchCandidate(vehicle, shipment, feasibility, float("-inf"), 0.0)

    total_miles = feasibility.deadhead_miles + feasibility.loaded_miles
    utilization = shipment.weight_lbs / vehicle.max_weight_lbs if vehicle.max_weight_lbs else 0.0
    urgency = 0.0
    if shipment.pickup_window.end > dispatch_start:
        hours_left = (shipment.pickup_window.end - dispatch_start).total_seconds() / 3600
        urgency = 1.0 / max(hours_left, 0.25)
    economics_profit = shipment.revenue
    if cost_inputs is not None:
        economics_profit = load_economics(
            shipment.revenue,
            feasibility.loaded_miles,
            feasibility.deadhead_miles,
            feasibility.travel_minutes / 60,
            cost_inputs,
        ).gross_profit

    profit_signal = economics_profit / max(abs(shipment.revenue), 1.0)
    deadhead_signal = 1.0 / max(total_miles, 1.0)
    score = (
        config.profit_weight * profit_signal
        + config.deadhead_weight * deadhead_signal
        + config.urgency_weight * urgency
        + config.utilization_weight * utilization
    )
    return DispatchCandidate(vehicle, shipment, feasibility, score, economics_profit)


def audit_candidate(candidate: DispatchCandidate) -> DispatchAudit:
    """Independent deterministic gate for a proposed dispatch assignment."""
    checks: list[str] = []
    errors: list[str] = []
    if not candidate.feasibility.feasible:
        errors.extend(candidate.feasibility.reasons)
    else:
        checks.append("FEASIBILITY_PASSED")
    if candidate.feasibility.deadhead_miles < 0 or candidate.feasibility.loaded_miles < 0:
        errors.append("NEGATIVE_DISTANCE")
    if candidate.feasibility.travel_minutes < 0:
        errors.append("NEGATIVE_TRAVEL_TIME")
    if not math.isfinite(candidate.score):
        errors.append("NON_FINITE_SCORE")
    if candidate.estimated_profit < -abs(candidate.shipment.revenue):
        errors.append("PROFIT_RECONCILIATION_FAILED")
    return DispatchAudit(not errors, tuple(checks), tuple(errors))


def assign_best_vehicle(
    shipment: Shipment,
    vehicles: list[Vehicle],
    dispatch_start: datetime,
    provider: RouteProvider,
    config: DispatchConfig | None = None,
    cost_inputs: CostInputs | None = None,
) -> DispatchCandidate | None:
    """Return the highest-scoring feasible vehicle assignment."""
    candidates = [
        score_candidate(
            vehicle,
            shipment,
            check_feasibility(vehicle, shipment, dispatch_start, provider, config),
            dispatch_start,
            config,
            cost_inputs,
        )
        for vehicle in vehicles
    ]
    feasible = [candidate for candidate in candidates if candidate.feasibility.feasible and audit_candidate(candidate).passed]
    if not feasible:
        return None
    return max(feasible, key=lambda candidate: (candidate.score, candidate.estimated_profit, -candidate.feasibility.deadhead_miles, candidate.vehicle.vehicle_id))


def plan_multi_stop(
    shipments: list[Shipment],
    vehicle: Vehicle,
    dispatch_start: datetime,
    provider: RouteProvider,
    config: DispatchConfig | None = None,
    cost_inputs: CostInputs | None = None,
) -> DispatchPlan:
    """Build a deterministic pickup-delivery sequence by repeatedly selecting the best feasible next load."""
    config = config or DispatchConfig()
    config.validate()
    remaining = list(shipments)
    selected: list[Shipment] = []
    candidates: list[DispatchCandidate] = []
    current_time = dispatch_start
    current_location = vehicle.current_location
    total_miles = 0.0
    total_minutes = 0.0
    revenue = 0.0
    profit = 0.0

    while remaining:
        working_vehicle = Vehicle(
            vehicle.vehicle_id,
            vehicle.vehicle_type,
            vehicle.max_weight_lbs,
            vehicle.max_volume_cuft,
            VehicleStatus.AVAILABLE,
            current_location,
            vehicle.fuel_economy_mpg,
            vehicle.operating_cost_per_mile,
        )
        feasible_candidates = []
        for shipment in remaining:
            candidate = score_candidate(
                working_vehicle,
                shipment,
                check_feasibility(working_vehicle, shipment, current_time, provider, config),
                current_time,
                config,
                cost_inputs,
            )
            if candidate.feasibility.feasible and audit_candidate(candidate).passed:
                feasible_candidates.append(candidate)
        if not feasible_candidates:
            break

        best = max(feasible_candidates, key=lambda c: (c.score, c.estimated_profit, -c.feasibility.deadhead_miles, c.shipment.shipment_id))
        candidates.append(best)
        selected.append(best.shipment)
        remaining.remove(best.shipment)
        total_miles += best.feasibility.deadhead_miles + best.feasibility.loaded_miles
        total_minutes += best.feasibility.travel_minutes + config.pickup_service_minutes + config.delivery_service_minutes
        revenue += best.shipment.revenue
        profit += best.estimated_profit
        current_time = (best.feasibility.delivery_arrival or current_time) + timedelta(minutes=config.delivery_service_minutes)
        current_location = best.shipment.delivery

    return DispatchPlan(vehicle, tuple(selected), tuple(candidates), total_miles, total_minutes, revenue, profit)
