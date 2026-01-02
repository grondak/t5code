"""Test basic starship agent behavior."""

import simpy
import pytest
from t5code import GameState as gs_module, T5Starship, T5World
from t5code.GameState import GameState
from t5sim import StarshipAgent, StarshipState


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


@pytest.fixture
def mock_simulation(game_state):
    """Create mock simulation object."""
    from unittest.mock import Mock
    sim = Mock()
    sim.game_state = game_state
    sim.record_cargo_sale = Mock()
    return sim


def test_starship_agent_initialization(game_state, mock_simulation):
    """Test that agent initializes correctly."""
    env = simpy.Environment()
    from t5code import T5ShipClass

    ship_class_dict = next(iter(game_state.ship_classes.values()))
    class_name = ship_class_dict["class_name"]
    ship_class = T5ShipClass(class_name, ship_class_dict)
    ship = T5Starship("Test Ship", "Rhylanor", ship_class)

    agent = StarshipAgent(env, ship, mock_simulation)

    assert agent.ship == ship
    assert agent.state == StarshipState.DOCKED
    assert agent.voyage_count == 0


def test_starship_agent_state_transitions(game_state, mock_simulation):
    """Test that agent transitions through states."""
    env = simpy.Environment()
    from t5code import T5ShipClass

    ship_class_dict = next(iter(game_state.ship_classes.values()))
    class_name = ship_class_dict["class_name"]
    ship_class = T5ShipClass(class_name, ship_class_dict)
    ship = T5Starship("Test Ship", "Rhylanor", ship_class)
    ship.credit(1_000_000)
    ship.set_course_for("Jae Tellona")

    agent = StarshipAgent(env, ship, mock_simulation)

    # Run simulation for a short time
    env.run(until=1.0)  # 1 day

    # Agent should have progressed through some states
    assert agent.state != StarshipState.DOCKED


def test_starship_agent_with_no_speculation(game_state, mock_simulation):
    """Test agent with cargo speculation disabled."""
    env = simpy.Environment()
    from t5code import T5ShipClass

    ship_class_dict = next(iter(game_state.ship_classes.values()))
    class_name = ship_class_dict["class_name"]
    ship_class = T5ShipClass(class_name, ship_class_dict)
    ship = T5Starship("Test Ship", "Rhylanor", ship_class)
    ship.credit(1_000_000)
    ship.set_course_for("Jae Tellona")

    agent = StarshipAgent(
        env, ship, mock_simulation, speculate_cargo=False
    )

    assert agent.speculate_cargo is False

    # Run simulation briefly
    env.run(until=1.0)

    # Agent should still work without speculation
    assert agent.state != StarshipState.DOCKED
