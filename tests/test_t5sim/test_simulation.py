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
