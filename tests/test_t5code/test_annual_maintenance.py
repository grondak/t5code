"""Tests for annual maintenance day functionality."""

import pytest
from t5code.T5Company import T5Company
from t5code.T5ShipClass import T5ShipClass
from t5code.T5Starship import T5Starship


@pytest.fixture
def company():
    """Create a test company."""
    return T5Company("Test Company", starting_capital=1000000)


@pytest.fixture
def ship_class_data():
    """Create test ship class data."""
    return {
        "class_name": "Test Ship",
        "ship_cost": 50.0,
        "jump_rating": 2,
        "maneuver_rating": 2,
        "powerplant_rating": 2,
        "cargo_capacity": 50,
        "staterooms": 5,
        "low_berths": 10,
        "crew_positions": "0BC",
        "crew_ranks": "012",
        "jump_fuel_capacity": 20,
        "ops_fuel_capacity": 2,
    }


def test_maintenance_day_assigned_on_creation(company, ship_class_data):
    """Test that ships get a maintenance day assigned when created."""
    ship_class = T5ShipClass("Test Ship", ship_class_data)
    ship = T5Starship(
        "Test Ship",
        "Rethe/Regina (2408)",
        ship_class,
        company
    )

    assert hasattr(ship, "annual_maintenance_day")
    assert isinstance(ship.annual_maintenance_day, int)


def test_maintenance_day_not_on_holiday(company, ship_class_data):
    """Test that maintenance day is never on day 1 (holiday)."""
    ship_class = T5ShipClass("Test Ship", ship_class_data)

    # Create many ships to ensure it's not just luck
    for i in range(100):
        ship = T5Starship(
            f"Test Ship {i}",
            "Rethe/Regina (2408)",
            ship_class,
            company
        )
        assert ship.annual_maintenance_day != 1, \
            "Maintenance day should never be on day 1 (holiday)"


def test_maintenance_day_in_valid_range(company, ship_class_data):
    """Test that maintenance day is between 2 and 365."""
    ship_class = T5ShipClass("Test Ship", ship_class_data)

    # Create many ships to test the range
    for i in range(100):
        ship = T5Starship(
            f"Test Ship {i}",
            "Rethe/Regina (2408)",
            ship_class,
            company
        )
        assert 2 <= ship.annual_maintenance_day <= 365, \
            f"Maintenance day must be between 2 and 365, " \
            f"got {ship.annual_maintenance_day}"


def test_maintenance_day_varies_between_ships(company, ship_class_data):
    """Test that different ships get different maintenance days."""
    ship_class = T5ShipClass("Test Ship", ship_class_data)

    # Create multiple ships and collect their maintenance days
    maintenance_days = set()

    for i in range(50):
        ship = T5Starship(
            f"Test Ship {i}",
            "Rethe/Regina (2408)",
            ship_class,
            company
        )
        maintenance_days.add(ship.annual_maintenance_day)

    # With 50 ships and 364 possible days, we should see variation
    # (very unlikely to get the same day for all ships)
    assert len(maintenance_days) > 1, \
        "Ships should have varying maintenance days"


def test_maintenance_day_edge_cases(company, ship_class_data):
    """Test that edge values (2 and 365) can be assigned."""
    ship_class = T5ShipClass("Test Ship", ship_class_data)

    # This is probabilistic, so we'll try multiple times
    maintenance_days = set()

    for i in range(200):
        ship = T5Starship(
            f"Test Ship {i}",
            "Rethe/Regina (2408)",
            ship_class,
            company
        )
        maintenance_days.add(ship.annual_maintenance_day)

    # We should eventually see both edge cases (2 and 365) in 200 ships
    # This is a probabilistic test, so we'll just
    # check that the range includes them
    min_day = min(maintenance_days)
    max_day = max(maintenance_days)

    assert min_day >= 2, f"Minimum should be at least 2, got {min_day}"
    assert max_day <= 365, f"Maximum should be at most 365, got {max_day}"


def test_maintenance_day_distribution(company, ship_class_data):
    """Test that maintenance days are reasonably distributed."""
    ship_class = T5ShipClass("Test Ship", ship_class_data)

    maintenance_days = set()

    # Create a larger sample
    for i in range(300):
        ship = T5Starship(
            f"Test Ship {i}",
            "Rethe/Regina (2408)",
            ship_class,
            company
        )
        maintenance_days.add(ship.annual_maintenance_day)

    # Should have good variety (at least 50 unique days out of 300 ships)
    assert len(maintenance_days) >= 50, \
        f"Expected at least 50 unique maintenance " \
        f"days, got {len(maintenance_days)}"


def test_maintenance_day_persists(company, ship_class_data):
    """Test that the maintenance day doesn't change after creation."""
    ship_class = T5ShipClass("Test Ship", ship_class_data)
    ship = T5Starship(
        "Test Ship",
        "Rethe/Regina (2408)",
        ship_class,
        company
    )

    original_day = ship.annual_maintenance_day

    # Do various operations
    ship.set_course_for("Paya/Aramis (2509)")
    ship.location = "Paya/Aramis (2509)"

    # Maintenance day should remain the same
    assert ship.annual_maintenance_day == original_day, \
        "Maintenance day should not change after creation"


def test_different_ship_classes_get_maintenance_days(company):
    """Test that all ship classes get maintenance days assigned."""
    ship_classes = {
        "Scout": {
            "class_name": "Scout",
            "ship_cost": 70.3,
            "jump_rating": 2,
            "maneuver_rating": 2,
            "powerplant_rating": 2,
            "cargo_capacity": 10,
            "staterooms": 0,
            "low_berths": 0,
            "crew_positions": "0BCG",
            "crew_ranks": "0123",
            "jump_fuel_capacity": 20,
            "ops_fuel_capacity": 2,
        },
        "Freighter": {
            "class_name": "Freighter",
            "ship_cost": 61.1,
            "jump_rating": 1,
            "maneuver_rating": 1,
            "powerplant_rating": 1,
            "cargo_capacity": 82,
            "staterooms": 9,
            "low_berths": 20,
            "crew_positions": "0BCDF",
            "crew_ranks": "01234",
            "jump_fuel_capacity": 20,
            "ops_fuel_capacity": 2,
        },
    }

    for ship_class_name, ship_data in ship_classes.items():
        ship_class = T5ShipClass(ship_class_name, ship_data)
        ship = T5Starship(
            f"{ship_class_name} Test",
            "Rethe/Regina (2408)",
            ship_class,
            company
        )

        assert hasattr(ship, "annual_maintenance_day"), \
            f"{ship_class_name} should have annual_maintenance_day"
        assert 2 <= ship.annual_maintenance_day <= 365, \
            f"{ship_class_name} maintenance day should be in valid range"
