"""Tests for edge cases to improve coverage."""

import pytest
from unittest.mock import patch
from t5code import GameState as gs_module, T5World
from t5code.GameState import GameState
from t5sim import Simulation
from t5sim.starship_states import print_voyage_summary


@pytest.fixture
def game_state():
    """Create initialized game state."""
    gs = GameState()
    # Load raw data
    raw_worlds = gs_module.load_and_parse_t5_map("resources/t5_map.txt")
    raw_ships = gs_module.load_and_parse_t5_ship_classes(
        "resources/t5_ship_classes.csv"
    )
    # Convert to objects
    gs.world_data = T5World.load_all_worlds(raw_worlds)
    gs.ship_classes = raw_ships
    return gs


def test_isolated_world_fallback(game_state):
    """Test that setup handles worlds with no reachable destinations.

    This tests the fallback path where no starting world with
    destinations can be found after 100 attempts (simulated by
    mocking to always return empty list).
    """
    from t5code import T5Starship

    sim = Simulation(game_state, num_ships=1, duration_days=1.0)

    # Patch T5Starship to always return empty jump range
    with patch.object(T5Starship, 'get_worlds_in_jump_range',
                      return_value=[]):
        # Should fall back to random world even with no destinations
        sim.setup()

        # Should have created 1 agent
        assert len(sim.agents) == 1
        # Ship destination should be set to current location (fallback)
        agent = sim.agents[0]
        assert agent.ship.destination == agent.ship.location


def test_no_profitable_destinations():
    """Test setup when no profitable destinations are found.

    This tests the else branch where find_profitable_destinations
    returns empty list, so we fall back to random reachable world.
    """
    from t5code import T5Starship

    gs = GameState()
    raw_worlds = gs_module.load_and_parse_t5_map("resources/t5_map.txt")
    raw_ships = gs_module.load_and_parse_t5_ship_classes(
        "resources/t5_ship_classes.csv"
    )
    gs.world_data = T5World.load_all_worlds(raw_worlds)
    gs.ship_classes = raw_ships

    sim = Simulation(gs, num_ships=1, duration_days=1.0)

    # Mock find_profitable_destinations to return empty
    with patch.object(T5Starship, 'find_profitable_destinations',
                      return_value=[]):
        sim.setup()

        # Should still have created agent with destination
        assert len(sim.agents) == 1
        assert sim.agents[0].ship.destination is not None


def test_print_voyage_summary():
    """Test the print_voyage_summary function from starship_states."""
    # This tests the if __name__ == "__main__" path
    import io
    import sys

    # Capture stdout
    captured_output = io.StringIO()
    sys.stdout = captured_output

    try:
        print_voyage_summary()
        output = captured_output.getvalue()

        # Check that output contains expected elements
        assert "MERCHANT STARSHIP TRADING VOYAGE" in output
        assert "DOCKED" in output
        assert "JUMPING" in output
        assert "Total voyage time" in output
    finally:
        sys.stdout = sys.__stdout__


def test_run_main_entry_point():
    """Test the main() function entry point in run.py."""
    from t5sim.run import main
    import sys

    # Mock sys.argv to provide test arguments
    original_argv = sys.argv
    try:
        sys.argv = [
            'run.py',
            '--ships', '1',
            '--days', '1',
            '--map', 'tests/test_t5code/t5_test_map.txt',
            '--ships-file', 'resources/t5_ship_classes.csv'
        ]

        # Should run without error
        main()

    finally:
        sys.argv = original_argv
