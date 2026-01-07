"""Shared test fixtures for t5sim tests."""

import pytest
from t5code.GameState import GameState, load_and_parse_t5_map
from t5code.T5World import T5World


@pytest.fixture
def test_ship_data():
    """Ship class test data (small scout ship)."""
    return {
        "small": {
            "class_name": "small",
            "ship_cost": 25.0,
            "jump_rating": 1,
            "maneuver_rating": 2,
            "cargo_capacity": 10,
            "staterooms": 2,
            "low_berths": 0,
            "crew_positions": ["A", "B", "C"],  # Pilot, Astrogator, Engineer
            "jump_fuel_capacity": 20,
            "ops_fuel_capacity": 2,
            "role": "civilian",
        },
        "large": {
            "class_name": "large",
            "ship_cost": 150.0,
            "jump_rating": 3,
            "maneuver_rating": 3,
            "cargo_capacity": 200,
            "staterooms": 10,
            "low_berths": 50,
            "crew_positions": ["0", "A", "B", "B", "C", "C", "C", "D"],
            "jump_fuel_capacity": 60,
            "ops_fuel_capacity": 6,
            "role": "military",
        },
        "specialized": {
            "class_name": "specialized",
            "ship_cost": 100.0,
            "jump_rating": 2,
            "maneuver_rating": 2,
            "cargo_capacity": 50,
            "staterooms": 5,
            "low_berths": 0,
            "crew_positions": ["A", "B", "C", "D"],
            "jump_fuel_capacity": 40,
            "ops_fuel_capacity": 4,
            "role": "specialized",
        },
    }


@pytest.fixture
def setup_test_gamestate(test_ship_data):
    """Setup GameState instance for tests that need world and ship data."""
    MAP_FILE = "tests/test_t5code/t5_test_map.txt"
    game_state = GameState()
    game_state.world_data = T5World.load_all_worlds(
        load_and_parse_t5_map(MAP_FILE))
    game_state.ship_classes = test_ship_data
    return game_state
