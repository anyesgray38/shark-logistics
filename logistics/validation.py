"""Deterministic validation and audit-friendly checks."""

from dataclasses import dataclass

from .models import Shipment, Vehicle


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    field: str | None = None


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    issues: tuple[ValidationIssue, ...] = ()

    @classmethod
    def from_issues(cls, issues: list[ValidationIssue]) -> "ValidationResult":
        return cls(valid=not issues, issues=tuple(issues))


def validate_shipment(shipment: Shipment) -> ValidationResult:
    issues: list[ValidationIssue] = []
    if not shipment.shipment_id.strip():
        issues.append(ValidationIssue("SHIPMENT_ID_REQUIRED", "Shipment ID is required.", "shipment_id"))
    if not shipment.customer_id.strip():
        issues.append(ValidationIssue("CUSTOMER_ID_REQUIRED", "Customer ID is required.", "customer_id"))
    if shipment.weight_lbs < 0:
        issues.append(ValidationIssue("NEGATIVE_WEIGHT", "Shipment weight cannot be negative.", "weight_lbs"))
    if shipment.volume_cuft is not None and shipment.volume_cuft < 0:
        issues.append(ValidationIssue("NEGATIVE_VOLUME", "Shipment volume cannot be negative.", "volume_cuft"))
    if shipment.revenue < 0:
        issues.append(ValidationIssue("NEGATIVE_REVENUE", "Shipment revenue cannot be negative.", "revenue"))
    if shipment.pickup_window.start >= shipment.pickup_window.end:
        issues.append(ValidationIssue("INVALID_PICKUP_WINDOW", "Pickup window start must precede end.", "pickup_window"))
    if shipment.delivery_window and shipment.delivery_window.start >= shipment.delivery_window.end:
        issues.append(ValidationIssue("INVALID_DELIVERY_WINDOW", "Delivery window start must precede end.", "delivery_window"))
    return ValidationResult.from_issues(issues)


def validate_vehicle(vehicle: Vehicle) -> ValidationResult:
    issues: list[ValidationIssue] = []
    if not vehicle.vehicle_id.strip():
        issues.append(ValidationIssue("VEHICLE_ID_REQUIRED", "Vehicle ID is required.", "vehicle_id"))
    if vehicle.max_weight_lbs <= 0:
        issues.append(ValidationIssue("INVALID_WEIGHT_CAPACITY", "Vehicle weight capacity must be positive.", "max_weight_lbs"))
    if vehicle.max_volume_cuft is not None and vehicle.max_volume_cuft <= 0:
        issues.append(ValidationIssue("INVALID_VOLUME_CAPACITY", "Vehicle volume capacity must be positive.", "max_volume_cuft"))
    if vehicle.fuel_economy_mpg is not None and vehicle.fuel_economy_mpg <= 0:
        issues.append(ValidationIssue("INVALID_FUEL_ECONOMY", "Fuel economy must be positive.", "fuel_economy_mpg"))
    if vehicle.operating_cost_per_mile is not None and vehicle.operating_cost_per_mile < 0:
        issues.append(ValidationIssue("NEGATIVE_OPERATING_COST", "Operating cost cannot be negative.", "operating_cost_per_mile"))
    return ValidationResult.from_issues(issues)
