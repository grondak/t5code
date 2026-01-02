"""Test cargo speculation policy feature."""

import pytest
from t5sim import Simulation
from t5code.GameState import GameState, load_and_parse_t5_map
from t5code.T5World import T5World


@pytest.fixture
def game_state():
    """Create a test game state."""
    gs = GameState()
    MAP_FILE = "tests/test_t5code/t5_test_map.txt"
    raw_worlds = load_and_parse_t5_map(MAP_FILE)
    gs.world_data = T5World.load_all_worlds(raw_worlds)
    gs.ship_classes = {
        "FreeTrader": {
            "class_name": "FreeTrader",
            "tonnage": 200,
            "cargo_capacity": 82,
            "staterooms": 10,
            "low_berths": 0,
            "jump_rating": 2,
            "maneuver_rating": 1,
        }
    }
    return gs


def test_simulation_with_no_speculation(game_state):
    """Test simulation with 100% no-speculation policy."""
    sim = Simulation(
        game_state,
        num_ships=3,
        duration_days=5.0,
        speculate_cargo_pct=0.0
    )
    sim.setup()

    # All agents should have speculate_cargo=False
    for agent in sim.agents:
        assert agent.speculate_cargo is False


def test_simulation_with_mixed_speculation(game_state):
    """Test simulation with 50% no-speculation policy."""
    sim = Simulation(
        game_state,
        num_ships=4,
        duration_days=5.0,
        speculate_cargo_pct=0.5
    )
    sim.setup()

    # First 2 should speculate (50% of 4)
    assert sim.agents[0].speculate_cargo is True
    assert sim.agents[1].speculate_cargo is True

    # Last 2 should not speculate
    assert sim.agents[2].speculate_cargo is False
    assert sim.agents[3].speculate_cargo is False


def test_simulation_run_with_no_speculation(game_state):
    """Test running simulation with no-speculation policy."""
    sim = Simulation(
        game_state,
        num_ships=2,
        duration_days=1.0,
        speculate_cargo_pct=0.0
    )
    results = sim.run()

    # Verify results structure
    assert "total_profit" in results
    assert "cargo_sales" in results
    assert results["cargo_sales"] == 0  # No cargo speculation
    assert results["num_ships"] == 2


def test_run_simulation_function():
    """Test the run_simulation convenience function."""
    from t5sim.simulation import run_simulation

    results = run_simulation(
        map_file="tests/test_t5code/t5_test_map.txt",
        ship_classes_file="resources/t5_ship_classes.csv",
        num_ships=2,
        duration_days=1.0,
        speculate_cargo_pct=0.5
    )

    assert results["num_ships"] == 2
    assert "total_profit" in results
    assert "ships" in results
    assert len(results["ships"]) == 2
