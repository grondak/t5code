"""Tests to cover fuel-related edge cases in starship_agent.py."""

import simpy
import pytest
from t5code import GameState as gs_module, T5Starship, T5World
from t5code.T5Company import T5Company
from t5code.GameState import GameState
from t5code.T5ShipClass import T5ShipClass
from t5sim import StarshipAgent, StarshipState


@pytest.fixture
def game_state():
    """Create initialized game state."""
    gs = GameState()
    raw_worlds = gs_module.load_and_parse_t5_map("resources/t5_map.txt")
    raw_ships = gs_module.load_and_parse_t5_ship_classes(
        "resources/t5_ship_classes.csv"
    )
    gs.world_data = T5World.load_all_worlds(raw_worlds)
    gs.ship_classes = raw_ships
    return gs


@pytest.fixture
def mock_simulation(game_state):
    """Create mock simulation object."""
    from unittest.mock import Mock
    sim = Mock()
    sim.game_state = game_state
    sim.verbose = True  # Enable verbose for some tests
    sim.record_cargo_sale = Mock()
    sim.starting_day = 1
    return sim


@pytest.fixture
def non_verbose_simulation(game_state):
    """Create non-verbose mock simulation object."""
    from unittest.mock import Mock
    sim = Mock()
    sim.game_state = game_state
    sim.verbose = False  # Disable verbose
    sim.record_cargo_sale = Mock()
    sim.starting_day = 1
    return sim


def test_fuel_loading_non_verbose(game_state, non_verbose_simulation):
    """Test fuel loading with verbose=False to cover early return."""
    env = simpy.Environment()

    ship_class_dict = next(iter(game_state.ship_classes.values()))
    class_name = ship_class_dict["class_name"]
    ship_class = T5ShipClass(class_name, ship_class_dict)
    company = T5Company("Test Company", starting_capital=1_000_000)
    ship = T5Starship("Test Ship", "Rhylanor", ship_class, owner=company)
    ship.credit(0, 1_000_000)
    ship.set_course_for("Jae Tellona")

    # Drain some fuel so refueling is needed
    initial_jump = ship.jump_fuel_capacity // 2
    initial_ops = ship.ops_fuel_capacity // 2
    ship.jump_fuel = initial_jump
    ship.ops_fuel = initial_ops

    agent = StarshipAgent(
        env, ship, non_verbose_simulation,
        starting_state=StarshipState.LOADING_FUEL
    )

    # Run through fuel loading state
    env.run(until=1.0)

    # Should have refueled despite non-verbose mode
    assert ship.jump_fuel > initial_jump or ship.ops_fuel > initial_ops

    # State should progress
    assert agent.state != StarshipState.LOADING_FUEL


def test_insufficient_funds_for_fuel(game_state, mock_simulation, capsys):
    """Test ship going broke when can't afford fuel."""
    env = simpy.Environment()

    ship_class_dict = next(iter(game_state.ship_classes.values()))
    class_name = ship_class_dict["class_name"]
    ship_class = T5ShipClass(class_name, ship_class_dict)
    company = T5Company("Broke Company", starting_capital=100)
    ship = T5Starship("Broke Ship", "Rhylanor", ship_class, owner=company)
    ship.credit(0, 100)  # Only Cr100
    ship.set_course_for("Jae Tellona")

    # Drain fuel so ship needs to refuel
    ship.jump_fuel = 0
    ship.ops_fuel = 0

    agent = StarshipAgent(
        env, ship, mock_simulation,
        starting_state=StarshipState.LOADING_FUEL
    )

    # Run through fuel loading - should fail and mark broke
    env.run(until=1.0)

    # Ship should be marked broke
    assert agent.broke is True

    # Check verbose output
    captured = capsys.readouterr()
    assert "insufficient funds for fuel" in captured.out
    assert "suspending operations" in captured.out


def test_broke_ship_sleeps(game_state, mock_simulation):
    """Test that broke ships sleep and don't execute normal operations."""
    env = simpy.Environment()

    ship_class_dict = next(iter(game_state.ship_classes.values()))
    class_name = ship_class_dict["class_name"]
    ship_class = T5ShipClass(class_name, ship_class_dict)
    company = T5Company("Test Company", starting_capital=1_000_000)
    ship = T5Starship("Test Ship", "Rhylanor", ship_class, owner=company)
    ship.set_course_for("Jae Tellona")

    agent = StarshipAgent(env, ship, mock_simulation)

    # Manually mark ship as broke
    agent.broke = True
    initial_state = agent.state

    # Run for a short time
    env.run(until=5.0)

    # State should not have changed (ship is sleeping)
    assert agent.state == initial_state


def test_cargo_purchase_skips_when_insufficient_fuel_funds(
    game_state, mock_simulation, capsys
):
    """Test cargo loading skips when can't afford fuel."""
    env = simpy.Environment()

    ship_class_dict = next(iter(game_state.ship_classes.values()))
    class_name = ship_class_dict["class_name"]
    ship_class = T5ShipClass(class_name, ship_class_dict)

    # Calculate fuel cost first
    # For Scout: 20t jump + 2t ops = 22t * 500 = Cr11,000
    jump_fuel_capacity = ship_class_dict.get("jump_fuel_capacity", 20)
    ops_fuel_capacity = ship_class_dict.get("ops_fuel_capacity", 2)
    fuel_cost = (jump_fuel_capacity + ops_fuel_capacity) * 500

    # Start company with just under fuel cost
    company = T5Company("Poor Company", starting_capital=fuel_cost - 100)
    ship = T5Starship("Poor Ship", "Rhylanor", ship_class, owner=company)
    ship.set_course_for("Jae Tellona")

    # Drain fuel so ship will need refill
    ship.jump_fuel = 0
    ship.ops_fuel = 0

    _agent = StarshipAgent(  # noqa: F841
        env, ship, mock_simulation,
        starting_state=StarshipState.LOADING_CARGO
    )

    # Run through cargo loading state
    env.run(until=1.0)

    # Check verbose output shows skipping
    captured = capsys.readouterr()
    assert "skipping cargo purchase" in captured.out
    assert "for fuel" in captured.out


def test_cargo_purchase_breaks_on_insufficient_funds(game_state,
                                                     mock_simulation):
    """Test cargo loading breaks loop on InsufficientFundsError."""
    env = simpy.Environment()
    from t5code import T5NPC

    ship_class_dict = next(iter(game_state.ship_classes.values()))
    class_name = ship_class_dict["class_name"]
    ship_class = T5ShipClass(class_name, ship_class_dict)
    company = T5Company("Test Company", starting_capital=100_000)
    ship = T5Starship("Test Ship", "Rhylanor", ship_class, owner=company)
    ship.credit(0, 100_000)
    ship.set_course_for("Jae Tellona")

    # Add trader for better cargo access
    trader = T5NPC("Trader")
    trader.set_skill("Trader", 3)
    ship.hire_crew("trader", trader)

    agent = StarshipAgent(
        env, ship, mock_simulation,
        starting_state=StarshipState.LOADING_CARGO
    )

    # Run through cargo loading - might buy some but will stop
    env.run(until=1.0)

    # Should have progressed past cargo loading
    assert agent.state != StarshipState.LOADING_CARGO


def test_fuel_loading_with_full_tanks(game_state, mock_simulation, capsys):
    """Test fuel loading when tanks are already full."""
    env = simpy.Environment()

    ship_class_dict = next(iter(game_state.ship_classes.values()))
    class_name = ship_class_dict["class_name"]
    ship_class = T5ShipClass(class_name, ship_class_dict)
    company = T5Company("Test Company", starting_capital=1_000_000)
    ship = T5Starship("Test Ship", "Rhylanor", ship_class, owner=company)
    ship.credit(0, 1_000_000)
    ship.set_course_for("Jae Tellona")

    # Tanks are already full (default state)
    assert ship.jump_fuel == ship.jump_fuel_capacity
    assert ship.ops_fuel == ship.ops_fuel_capacity

    _agent = StarshipAgent(  # noqa: F841
        env, ship, mock_simulation,
        starting_state=StarshipState.LOADING_FUEL
    )

    # Run through fuel loading state
    env.run(until=1.0)

    # Check verbose output
    captured = capsys.readouterr()
    assert "tanks already full" in captured.out


def test_fuel_loading_partial_refuel(game_state, mock_simulation, capsys):
    """Test fuel loading when can only afford partial refuel."""
    env = simpy.Environment()

    ship_class_dict = next(iter(game_state.ship_classes.values()))
    class_name = ship_class_dict["class_name"]
    ship_class = T5ShipClass(class_name, ship_class_dict)
    company = T5Company("Test Company", starting_capital=5_000)
    ship = T5Starship("Test Ship", "Rhylanor", ship_class, owner=company)
    ship.set_course_for("Jae Tellona")

    # Drain fuel completely
    ship.jump_fuel = 0
    ship.ops_fuel = 0

    initial_balance = ship.owner.balance

    _agent = StarshipAgent(  # noqa: F841
        env, ship, mock_simulation,
        starting_state=StarshipState.LOADING_FUEL
    )

    # Run through fuel loading state only (not the full journey)
    env.run(until=0.4)  # Just past LOADING_FUEL duration (0.35 days)

    # Should have purchased SOME fuel but not full tanks
    affordable_tons = initial_balance // 500
    if affordable_tons > 0:
        # Check that some fuel was loaded
        total_fuel = ship.jump_fuel + ship.ops_fuel
        assert total_fuel > 0
        # Should have loaded exactly what we could afford
        assert total_fuel == affordable_tons

    # Check verbose output shows refueling
    captured = capsys.readouterr()
    if affordable_tons > 0:
        assert "refueled" in captured.out
    else:
        assert "insufficient funds" in captured.out


def test_jump_with_unknown_world_error(game_state, mock_simulation):
    """Test jump execution handles WorldNotFoundError gracefully."""
    env = simpy.Environment()
    from t5code import T5NPC

    ship_class_dict = next(iter(game_state.ship_classes.values()))
    class_name = ship_class_dict["class_name"]
    ship_class = T5ShipClass(class_name, ship_class_dict)
    company = T5Company("Test Company", starting_capital=1_000_000)
    ship = T5Starship("Test Ship", "Rhylanor", ship_class, owner=company)
    ship.credit(0, 1_000_000)

    # Set destination to non-existent world
    ship.set_course_for("Nonexistent World XYZ")

    # Add required crew
    pilot = T5NPC("Pilot")
    pilot.set_skill("Pilot", 2)
    ship.hire_crew("pilot", pilot)

    _agent = StarshipAgent(  # noqa: F841
        env, ship, mock_simulation,
        starting_state=StarshipState.JUMPING
    )

    initial_fuel = ship.jump_fuel

    # Run through jump state - should not crash
    env.run(until=8.0)

    # Ship should have "jumped" but fuel not consumed (unknown world)
    assert ship.jump_fuel == initial_fuel


def test_jump_exception_handling(game_state, mock_simulation, capsys):
    """Test jump execution handles generic exceptions."""
    env = simpy.Environment()
    from unittest.mock import patch

    ship_class_dict = next(iter(game_state.ship_classes.values()))
    class_name = ship_class_dict["class_name"]
    ship_class = T5ShipClass(class_name, ship_class_dict)
    company = T5Company("Test Company", starting_capital=1_000_000)
    ship = T5Starship("Test Ship", "Rhylanor", ship_class, owner=company)
    ship.credit(0, 1_000_000)
    ship.set_course_for("Jae Tellona")

    _agent = StarshipAgent(  # noqa: F841
        env, ship, mock_simulation,
        starting_state=StarshipState.JUMPING
    )

    # Patch ship.get_distance_to to raise generic exception
    with patch.object(ship,
                      'get_distance_to',
                      side_effect=Exception("Test error")):
        # Run through jump state - should not crash
        env.run(until=8.0)

        # Should have printed error
        captured = capsys.readouterr()
        assert "Jump error" in captured.out


def test_fuel_loading_exception_handling(game_state, mock_simulation, capsys):
    """Test fuel loading handles generic exceptions gracefully."""
    env = simpy.Environment()
    from unittest.mock import patch

    ship_class_dict = next(iter(game_state.ship_classes.values()))
    class_name = ship_class_dict["class_name"]
    ship_class = T5ShipClass(class_name, ship_class_dict)
    company = T5Company("Test Company", starting_capital=1_000_000)
    ship = T5Starship("Test Ship", "Rhylanor", ship_class, owner=company)
    ship.credit(0, 1_000_000)
    ship.set_course_for("Jae Tellona")

    # Drain some fuel
    ship.jump_fuel = ship.jump_fuel_capacity // 2

    _agent = StarshipAgent(  # noqa: F841
        env, ship, mock_simulation,
        starting_state=StarshipState.LOADING_FUEL
    )

    # Patch ship.debit to raise exception
    with patch.object(ship, 'debit', side_effect=Exception("Test fuel error")):
        # Run through fuel loading - should not crash
        env.run(until=1.0)

        # Should have printed error
        captured = capsys.readouterr()
        assert "Fuel loading error" in captured.out
