"""Deterministic fleet and shipment economics for Build 03.

All calculations are provider-independent and intentionally transparent so an
agent can propose a decision while deterministic logic verifies the numbers.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CostInputs:
    fuel_price_per_gallon: float
    fuel_economy_mpg: float
    driver_cost_per_hour: float = 0.0
    insurance_monthly: float = 0.0
    maintenance_per_mile: float = 0.0
    rental_monthly: float = 0.0
    other_monthly: float = 0.0

    def validate(self) -> None:
        if self.fuel_price_per_gallon < 0:
            raise ValueError("fuel_price_per_gallon cannot be negative")
        if self.fuel_economy_mpg <= 0:
            raise ValueError("fuel_economy_mpg must be positive")
        for name in ("driver_cost_per_hour", "insurance_monthly", "maintenance_per_mile", "rental_monthly", "other_monthly"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} cannot be negative")


@dataclass(frozen=True)
class LoadEconomics:
    revenue: float
    loaded_miles: float
    deadhead_miles: float
    travel_hours: float
    monthly_fixed_cost: float
    fuel_cost: float
    driver_cost: float
    maintenance_cost: float
    total_cost: float
    gross_profit: float
    profit_margin: float
    cost_per_total_mile: float


@dataclass(frozen=True)
class FleetEconomics:
    monthly_revenue: float
    monthly_miles: float
    monthly_fixed_cost: float
    fuel_cost: float
    driver_cost: float
    maintenance_cost: float
    total_cost: float
    operating_profit: float
    operating_margin: float
    cost_per_mile: float


def fuel_cost(miles: float, fuel_price_per_gallon: float, fuel_economy_mpg: float) -> float:
    if miles < 0:
        raise ValueError("miles cannot be negative")
    if fuel_price_per_gallon < 0:
        raise ValueError("fuel_price_per_gallon cannot be negative")
    if fuel_economy_mpg <= 0:
        raise ValueError("fuel_economy_mpg must be positive")
    return miles / fuel_economy_mpg * fuel_price_per_gallon


def monthly_fixed_cost(inputs: CostInputs) -> float:
    inputs.validate()
    return inputs.insurance_monthly + inputs.rental_monthly + inputs.other_monthly


def load_economics(
    revenue: float,
    loaded_miles: float,
    deadhead_miles: float,
    travel_hours: float,
    inputs: CostInputs,
    fixed_cost_allocation: float = 0.0,
) -> LoadEconomics:
    inputs.validate()
    if revenue < 0:
        raise ValueError("revenue cannot be negative")
    if loaded_miles < 0 or deadhead_miles < 0 or travel_hours < 0:
        raise ValueError("miles and travel_hours cannot be negative")
    if fixed_cost_allocation < 0:
        raise ValueError("fixed_cost_allocation cannot be negative")

    total_miles = loaded_miles + deadhead_miles
    fuel = fuel_cost(total_miles, inputs.fuel_price_per_gallon, inputs.fuel_economy_mpg)
    driver = travel_hours * inputs.driver_cost_per_hour
    maintenance = total_miles * inputs.maintenance_per_mile
    fixed = fixed_cost_allocation
    total = fuel + driver + maintenance + fixed
    profit = revenue - total
    margin = profit / revenue if revenue else 0.0
    cpm = total / total_miles if total_miles else 0.0
    return LoadEconomics(revenue, loaded_miles, deadhead_miles, travel_hours, fixed, fuel, driver, maintenance, total, profit, margin, cpm)


def fleet_economics(
    monthly_revenue: float,
    monthly_miles: float,
    monthly_hours: float,
    inputs: CostInputs,
    fixed_cost_override: Optional[float] = None,
) -> FleetEconomics:
    inputs.validate()
    if monthly_revenue < 0 or monthly_miles < 0 or monthly_hours < 0:
        raise ValueError("monthly revenue, miles, and hours cannot be negative")

    fixed = monthly_fixed_cost(inputs) if fixed_cost_override is None else fixed_cost_override
    if fixed < 0:
        raise ValueError("fixed_cost_override cannot be negative")
    fuel = fuel_cost(monthly_miles, inputs.fuel_price_per_gallon, inputs.fuel_economy_mpg)
    driver = monthly_hours * inputs.driver_cost_per_hour
    maintenance = monthly_miles * inputs.maintenance_per_mile
    total = fixed + fuel + driver + maintenance
    profit = monthly_revenue - total
    margin = profit / monthly_revenue if monthly_revenue else 0.0
    cpm = total / monthly_miles if monthly_miles else 0.0
    return FleetEconomics(monthly_revenue, monthly_miles, fixed, fuel, driver, maintenance, total, profit, margin, cpm)
