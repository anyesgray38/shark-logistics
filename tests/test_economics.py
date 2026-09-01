import pytest

from logistics.economics import CostInputs, fleet_economics, fuel_cost, load_economics


def inputs():
    return CostInputs(
        fuel_price_per_gallon=4.00,
        fuel_economy_mpg=10.0,
        driver_cost_per_hour=25.0,
        insurance_monthly=1250.0,
        maintenance_per_mile=0.15,
        rental_monthly=4000.0,
        other_monthly=250.0,
    )


def test_fuel_cost():
    assert fuel_cost(100, 4, 10) == pytest.approx(40.0)


def test_load_economics_includes_deadhead():
    result = load_economics(1000, 200, 50, 5, inputs())
    assert result.fuel_cost == pytest.approx(100.0)
    assert result.driver_cost == pytest.approx(125.0)
    assert result.maintenance_cost == pytest.approx(37.5)
    assert result.total_cost == pytest.approx(262.5)
    assert result.gross_profit == pytest.approx(737.5)
    assert result.cost_per_total_mile == pytest.approx(1.05)


def test_fleet_economics():
    result = fleet_economics(20000, 4000, 160, inputs())
    assert result.monthly_fixed_cost == pytest.approx(5500.0)
    assert result.fuel_cost == pytest.approx(1600.0)
    assert result.driver_cost == pytest.approx(4000.0)
    assert result.maintenance_cost == pytest.approx(600.0)
    assert result.total_cost == pytest.approx(11700.0)
    assert result.operating_profit == pytest.approx(8300.0)
    assert result.operating_margin == pytest.approx(0.415)


def test_invalid_inputs_are_rejected():
    with pytest.raises(ValueError):
        fuel_cost(100, 4, 0)
    with pytest.raises(ValueError):
        CostInputs(4, 10, driver_cost_per_hour=-1).validate()
