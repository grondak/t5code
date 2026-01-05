"""Test the main simulation orchestrator."""

import pytest
from t5code import GameState as gs_module, T5World
from t5code.GameState import GameState
from t5sim import Simulation


@pytest.fixture
def game_state():
    """Create initialized game state."""
    gs = GameState()
    # Load raw data
    raw_worlds = gs_module.load_and_parse_t5_map("resources/t5_map.txt")
    raw_ships = gs_module.load_and_parse_t5_ship_classes(
        "resources/t5_ship_classes.csv"
    )
    # Convert to objects (like GameDriver does)
    gs.world_data = T5World.load_all_worlds(raw_worlds)
    gs.ship_classes = raw_ships  # Ships stay as dicts, converted in simulation
    return gs


def test_simulation_initialization(game_state):
    """Test simulation initializes correctly."""
    sim = Simulation(game_state, num_ships=5, duration_days=10.0)

    assert sim.num_ships == 5
    assert sim.duration_days == pytest.approx(10.0)
    assert len(sim.agents) == 0  # Not setup yet


def test_simulation_setup(game_state):
    """Test simulation setup creates agents."""
    sim = Simulation(game_state, num_ships=3, duration_days=10.0)
    sim.setup()

    assert len(sim.agents) == 3
    # All ships should have crew and starting capital
    for agent in sim.agents:
        assert agent.ship.balance == sim.starting_capital
        assert len(agent.ship.crew) > 0


def test_simulation_run_short(game_state):
    """Test running simulation for short duration."""
    sim = Simulation(game_state, num_ships=2, duration_days=1.0)
    results = sim.run()

    assert results["num_ships"] == 2
    assert results["duration_days"] == pytest.approx(1.0)
    assert "total_voyages" in results
    assert "ships" in results
    assert len(results["ships"]) == 2


def test_simulation_record_cargo_sale(game_state):
    """Test recording cargo sales."""
    sim = Simulation(game_state, num_ships=1, duration_days=1.0)

    # Record a cargo sale
    sim.record_cargo_sale("TestShip", "Regina", 5000.0)

    # Check it was recorded
    assert len(sim.statistics["cargo_sales"]) == 1
    sale = sim.statistics["cargo_sales"][0]
    assert sale["ship"] == "TestShip"
    assert sale["location"] == "Regina"
    assert sale["profit"] == pytest.approx(5000.0)
    assert "time" in sale


def test_format_traveller_date_default_start(game_state):
    """Test Traveller date formatting with default starting date."""
    sim = Simulation(game_state, num_ships=1, duration_days=10.0)

    # Default is 360-1104
    assert sim.format_traveller_date(0.0) == "360-1104"
    assert sim.format_traveller_date(1.0) == "361-1104"
    assert sim.format_traveller_date(5.0) == "365-1104"
    assert sim.format_traveller_date(6.0) == "001-1105"  # Year rollover
    assert sim.format_traveller_date(10.0) == "005-1105"


def test_format_traveller_date_custom_start(game_state):
    """Test Traveller date formatting with custom starting date."""
    sim = Simulation(game_state, num_ships=1, duration_days=10.0,
                     starting_year=1105, starting_day=1)

    assert sim.format_traveller_date(0.0) == "001-1105"
    assert sim.format_traveller_date(1.0) == "002-1105"
    assert sim.format_traveller_date(364.0) == "365-1105"
    assert sim.format_traveller_date(365.0) == "001-1106"  # Year rollover


def test_format_traveller_date_mid_year(game_state):
    """Test Traveller date formatting starting mid-year."""
    sim = Simulation(game_state, num_ships=1, duration_days=10.0,
                     starting_year=1104, starting_day=180)

    assert sim.format_traveller_date(0.0) == "180-1104"
    assert sim.format_traveller_date(185.0) == "365-1104"
    assert sim.format_traveller_date(186.0) == "001-1105"  # Year rollover


def test_run_simulation_function():
    """Test the run_simulation convenience function
    loads data and runs simulation."""
    from t5sim.simulation import run_simulation

    # Call the actual function with test data
    results = run_simulation(
        map_file="tests/test_t5code/t5_test_map.txt",
        ship_classes_file="resources/t5_ship_classes.csv",
        num_ships=2,
        duration_days=1.0
    )

    # Verify it returns expected structure
    assert results["num_ships"] == 2
    assert results["duration_days"] == pytest.approx(1.0)
    assert "total_profit" in results
    assert "cargo_sales" in results
    assert "ships" in results
    assert len(results["ships"]) == 2
    assert "total_voyages" in results
