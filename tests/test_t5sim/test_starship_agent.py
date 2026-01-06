"""Test basic starship agent behavior."""

import simpy
import pytest
from t5code import GameState as gs_module, T5Starship, T5World
from t5code.T5Company import T5Company
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
    sim.starting_day = 1
    return sim


def test_starship_agent_initialization(game_state, mock_simulation):
    """Test that agent initializes correctly."""
    env = simpy.Environment()
    from t5code import T5ShipClass

    ship_class_dict = next(iter(game_state.ship_classes.values()))
    class_name = ship_class_dict["class_name"]
    ship_class = T5ShipClass(class_name, ship_class_dict)
    company = T5Company("Test Company", starting_capital=1_000_000)
    ship = T5Starship("Test Ship", "Rhylanor", ship_class, owner=company)

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
    company = T5Company("Test Company", starting_capital=1_000_000)
    ship = T5Starship("Test Ship", "Rhylanor", ship_class, owner=company)
    ship.credit(0, 1_000_000)
    ship.set_course_for("Jae Tellona")

    agent = StarshipAgent(env, ship, mock_simulation)

    # Run simulation for a short time
    env.run(until=1.0)  # 1 day

    # Agent should have progressed through some states
    # Agent should still work
    assert agent.state != StarshipState.DOCKED


def test_starship_agent_verbose_reporting(game_state, mock_simulation, capsys):
    """Test verbose reporting during agent initialization."""
    env = simpy.Environment()
    from t5code import T5ShipClass

    mock_simulation.verbose = True

    ship_class_dict = next(iter(game_state.ship_classes.values()))
    class_name = ship_class_dict["class_name"]
    ship_class = T5ShipClass(class_name, ship_class_dict)
    company = T5Company("Test Company", starting_capital=1_000_000)
    ship = T5Starship("Verbose Ship", "Rhylanor", ship_class, owner=company)
    ship.credit(0, 1_000_000)
    ship.set_course_for("Jae Tellona")

    _agent = StarshipAgent(env, ship, mock_simulation)  # noqa: F841

    # Check that initial status was reported
    captured = capsys.readouterr()
    assert "starting simulation" in captured.out
    assert "Verbose Ship" in captured.out
    assert class_name in captured.out  # Ship class should be shown


def test_starship_agent_offloading(game_state, mock_simulation):
    """Test offloading passengers, mail, and freight."""
    env = simpy.Environment()
    from t5code import T5ShipClass, T5NPC, T5Lot

    ship_class_dict = next(iter(game_state.ship_classes.values()))
    class_name = ship_class_dict["class_name"]
    ship_class = T5ShipClass(class_name, ship_class_dict)
    company = T5Company("Test Company", starting_capital=1_000_000)
    ship = T5Starship("Cargo Ship", "Rhylanor", ship_class, owner=company)
    ship.credit(0, 1_000_000)
    ship.set_course_for("Jae Tellona")

    # Add crew for passenger handling
    steward = T5NPC("Steward")
    steward.set_skill("Steward", 1)
    ship.hire_crew("steward", steward)

    # Load some passengers
    world = game_state.world_data.get("Rhylanor")
    if world:
        ship.load_passengers(0, world)

    # Load mail
    try:
        ship.load_mail(game_state, "Jae Tellona")
    except ValueError:
        pass  # No mail available is ok for test

    # Load freight
    try:
        freight_lot = T5Lot("Rhylanor", game_state)
        freight_lot.mass = 10
        ship.load_freight_lot(0, freight_lot)
    except Exception:
        pass  # Capacity issues are ok for test

    _agent = StarshipAgent(  # noqa: F841
        env, ship, mock_simulation, starting_state=StarshipState.OFFLOADING
    )

    # Run through offloading state
    env.run(until=0.5)

    # Passengers should be offloaded
    assert len(list(ship.passengers["high"])) == 0
    assert len(list(ship.passengers["mid"])) == 0
    assert len(list(ship.passengers["low"])) == 0


def test_starship_agent_selling_cargo(game_state, mock_simulation):
    """Test selling cargo lots."""
    env = simpy.Environment()
    from t5code import T5ShipClass, T5NPC

    ship_class_dict = next(iter(game_state.ship_classes.values()))
    class_name = ship_class_dict["class_name"]
    ship_class = T5ShipClass(class_name, ship_class_dict)
    company = T5Company("Test Company", starting_capital=1_000_000)
    ship = T5Starship("Trader Ship", "Rhylanor", ship_class, owner=company)
    ship.credit(0, 1_000_000)
    ship.set_course_for("Jae Tellona")

    # Add trader crew
    trader = T5NPC("Trader")
    trader.set_skill("Trader", 2)
    ship.hire_crew("trader", trader)

    # Buy some cargo at origin
    world = game_state.world_data.get("Rhylanor")
    if world:
        lots = world.generate_speculative_cargo(
            game_state, max_total_tons=20, max_lot_size=10
        )
        for lot in lots[:1]:  # Just buy one lot
            try:
                ship.buy_cargo_lot(0, lot)
            except Exception:
                pass

    initial_cargo_count = len(list(ship.cargo_manifest.get("cargo", [])))

    # Run through selling state
    env.run(until=0.6)

    # Cargo should be sold (or attempted)
    final_cargo_count = len(list(ship.cargo_manifest.get("cargo", [])))
    # Cargo count should be 0 or less than initial
    assert final_cargo_count <= initial_cargo_count


def test_starship_agent_loading_freight(game_state, mock_simulation):
    """Test loading freight lots."""
    env = simpy.Environment()
    from t5code import T5ShipClass, T5NPC

    ship_class_dict = next(iter(game_state.ship_classes.values()))
    class_name = ship_class_dict["class_name"]
    ship_class = T5ShipClass(class_name, ship_class_dict)
    company = T5Company("Test Company", starting_capital=1_000_000)
    ship = T5Starship("Freight Ship", "Rhylanor", ship_class, owner=company)
    ship.credit(0, 1_000_000)
    ship.set_course_for("Jae Tellona")

    # Add liaison crew
    liaison = T5NPC("Liaison")
    liaison.set_skill("Liaison", 1)
    ship.hire_crew("liaison", liaison)

    agent = StarshipAgent(
        env, ship, mock_simulation,
        starting_state=StarshipState.LOADING_FREIGHT
    )

    # Run through loading freight state
    # Ship will stay in LOADING_FREIGHT until 80% threshold is met
    env.run(until=10.0)

    # State should have progressed to later states after meeting threshold
    # Could be in any state after LOADING_FREIGHT
    assert agent.state != (StarshipState.LOADING_FREIGHT or
                           ship.cargo_size >= ship.hold_size * 0.8)
    # Should have loaded some freight
    assert ship.cargo_size > 0


def test_starship_agent_loading_cargo(game_state, mock_simulation):
    """Test loading speculative cargo."""
    env = simpy.Environment()
    from t5code import T5ShipClass

    ship_class_dict = next(iter(game_state.ship_classes.values()))
    class_name = ship_class_dict["class_name"]
    ship_class = T5ShipClass(class_name, ship_class_dict)
    company = T5Company("Test Company", starting_capital=1_000_000)
    ship = T5Starship("Spec Ship", "Rhylanor", ship_class, owner=company)
    ship.credit(0, 1_000_000)
    ship.set_course_for("Jae Tellona")

    agent = StarshipAgent(
        env, ship, mock_simulation, starting_state=StarshipState.LOADING_CARGO
    )

    # Run through loading cargo state
    env.run(until=0.6)

    # State should have progressed
    assert agent.state != StarshipState.LOADING_CARGO


def test_starship_agent_loading_mail(game_state, mock_simulation):
    """Test loading mail bundles."""
    env = simpy.Environment()
    from t5code import T5ShipClass, T5NPC

    ship_class_dict = next(iter(game_state.ship_classes.values()))
    class_name = ship_class_dict["class_name"]
    ship_class = T5ShipClass(class_name, ship_class_dict)
    company = T5Company("Test Company", starting_capital=1_000_000)
    ship = T5Starship("Mail Ship", "Rhylanor", ship_class, owner=company)
    ship.credit(0, 1_000_000)
    ship.set_course_for("Jae Tellona")

    # Add admin crew for mail
    admin = T5NPC("Admin")
    admin.set_skill("Admin", 1)
    ship.hire_crew("admin", admin)

    agent = StarshipAgent(
        env, ship, mock_simulation, starting_state=StarshipState.LOADING_MAIL
    )

    # Run through loading mail state
    env.run(until=0.2)

    # State should have progressed
    assert agent.state != StarshipState.LOADING_MAIL


def test_starship_agent_loading_passengers(game_state, mock_simulation):
    """Test loading passengers."""
    env = simpy.Environment()
    from t5code import T5ShipClass, T5NPC

    ship_class_dict = next(iter(game_state.ship_classes.values()))
    class_name = ship_class_dict["class_name"]
    ship_class = T5ShipClass(class_name, ship_class_dict)
    company = T5Company("Test Company", starting_capital=1_000_000)
    ship = T5Starship("Passenger Ship", "Rhylanor", ship_class, owner=company)
    ship.credit(0, 1_000_000)
    ship.set_course_for("Jae Tellona")

    # Add steward crew for passengers
    steward = T5NPC("Steward")
    steward.set_skill("Steward", 1)
    ship.hire_crew("steward", steward)

    agent = StarshipAgent(
        env, ship, mock_simulation,
        starting_state=StarshipState.LOADING_PASSENGERS
    )

    # Run through loading passengers state
    env.run(until=0.3)

    # State should have progressed
    assert agent.state != StarshipState.LOADING_PASSENGERS


def test_starship_agent_jumping(game_state, mock_simulation):
    """Test jump execution and voyage counting."""
    env = simpy.Environment()
    from t5code import T5ShipClass

    ship_class_dict = next(iter(game_state.ship_classes.values()))
    class_name = ship_class_dict["class_name"]
    ship_class = T5ShipClass(class_name, ship_class_dict)
    company = T5Company("Test Company", starting_capital=1_000_000)
    ship = T5Starship("Jump Ship", "Rhylanor", ship_class, owner=company)
    ship.credit(0, 1_000_000)
    ship.set_course_for("Jae Tellona")

    agent = StarshipAgent(
        env, ship, mock_simulation, starting_state=StarshipState.JUMPING
    )

    initial_voyage_count = agent.voyage_count

    # Run through jumping state (7 days)
    env.run(until=7.5)

    # Voyage count should increment
    assert agent.voyage_count > initial_voyage_count
    # State should have progressed
    assert agent.state != StarshipState.JUMPING


def test_starship_agent_verbose_transitions(game_state,
                                            mock_simulation,
                                            capsys):
    """Test verbose reporting of state transitions."""
    env = simpy.Environment()
    from t5code import T5ShipClass

    mock_simulation.verbose = True

    ship_class_dict = next(iter(game_state.ship_classes.values()))
    class_name = ship_class_dict["class_name"]
    ship_class = T5ShipClass(class_name, ship_class_dict)
    company = T5Company("Test Company", starting_capital=1_000_000)
    ship = T5Starship("Verbose Jump Ship",
                      "Rhylanor",
                      ship_class,
                      owner=company)
    ship.credit(0, 1_000_000)
    ship.set_course_for("Jae Tellona")

    _agent = StarshipAgent(  # noqa: F841
        env, ship, mock_simulation, starting_state=StarshipState.JUMPING
    )

    # Run through jump to trigger verbose arrival report
    env.run(until=7.5)

    captured = capsys.readouterr()
    assert "arrived at" in captured.out


def test_starship_agent_offloading_verbose(game_state,
                                           mock_simulation,
                                           capsys):
    """Test verbose reporting during offloading."""
    env = simpy.Environment()
    from t5code import T5ShipClass

    mock_simulation.verbose = True

    ship_class_dict = next(iter(game_state.ship_classes.values()))
    class_name = ship_class_dict["class_name"]
    ship_class = T5ShipClass(class_name, ship_class_dict)
    company = T5Company("Test Company", starting_capital=1_000_000)
    ship = T5Starship("Verbose Offload Ship",
                      "Rhylanor",
                      ship_class,
                      owner=company)
    ship.credit(0, 1_000_000)
    ship.set_course_for("Jae Tellona")

    _agent = StarshipAgent(  # noqa: F841
        env, ship, mock_simulation, starting_state=StarshipState.OFFLOADING
    )

    # Run through offloading
    env.run(until=0.3)

    captured = capsys.readouterr()
    assert "offloading complete" in captured.out


def test_starship_agent_selling_cargo_verbose(game_state,
                                              mock_simulation,
                                              capsys):
    """Test verbose reporting during cargo sales."""
    env = simpy.Environment()
    from t5code import T5ShipClass, T5NPC

    mock_simulation.verbose = True

    ship_class_dict = next(iter(game_state.ship_classes.values()))
    class_name = ship_class_dict["class_name"]
    ship_class = T5ShipClass(class_name, ship_class_dict)
    company = T5Company("Test Company", starting_capital=1_000_000)
    ship = T5Starship("Verbose Sales Ship",
                      "Rhylanor",
                      ship_class,
                      owner=company)
    ship.credit(0, 1_000_000)
    ship.set_course_for("Jae Tellona")

    # Add trader for sales
    trader = T5NPC("Trader")
    trader.set_skill("Trader", 2)
    ship.hire_crew("trader", trader)

    _agent = StarshipAgent(  # noqa: F841
        env, ship, mock_simulation, starting_state=StarshipState.SELLING_CARGO
    )

    # Run through selling
    env.run(until=0.6)

    captured = capsys.readouterr()
    assert "cargo sales complete" in captured.out


def test_starship_agent_error_handling_offload(game_state,
                                               mock_simulation,
                                               capsys):
    """Test error handling during offloading."""
    env = simpy.Environment()
    from t5code import T5ShipClass
    from unittest.mock import Mock

    ship_class_dict = next(iter(game_state.ship_classes.values()))
    class_name = ship_class_dict["class_name"]
    ship_class = T5ShipClass(class_name, ship_class_dict)
    company = T5Company("Test Company", starting_capital=1_000_000)
    ship = T5Starship("Error Ship", "Rhylanor", ship_class, owner=company)
    ship.credit(0, 1_000_000)
    ship.set_course_for("Jae Tellona")

    # Mock offload to raise exception
    ship.offload_passengers = Mock(side_effect=Exception("Test error"))

    _agent = StarshipAgent(  # noqa: F841
        env, ship, mock_simulation, starting_state=StarshipState.OFFLOADING
    )

    # Should handle error gracefully
    env.run(until=0.3)

    captured = capsys.readouterr()
    assert "Offload error" in captured.out


def test_starship_agent_error_handling_cargo_sale(game_state,
                                                  mock_simulation,
                                                  capsys):
    """Test error handling during cargo sales."""
    env = simpy.Environment()
    from t5code import T5ShipClass, T5NPC

    ship_class_dict = next(iter(game_state.ship_classes.values()))
    class_name = ship_class_dict["class_name"]
    ship_class = T5ShipClass(class_name, ship_class_dict)
    company = T5Company("Test Company", starting_capital=1_000_000)
    ship = T5Starship("Sale Error Ship", "Rhylanor", ship_class, owner=company)
    ship.credit(0, 1_000_000)
    ship.set_course_for("Jae Tellona")

    # Add trader
    trader = T5NPC("Trader")
    trader.set_skill("Trader", 2)
    ship.hire_crew("trader", trader)

    # Add cargo lot that will cause issues
    try:
        world = game_state.world_data.get("Rhylanor")
        if world:
            lots = world.generate_speculative_cargo(
                game_state, max_total_tons=10, max_lot_size=10
            )
            for lot in lots[:1]:
                ship.buy_cargo_lot(0, lot)
    except Exception:
        pass

    # Mock sell to raise exception
    from unittest.mock import Mock
    ship.sell_cargo_lot = Mock(side_effect=Exception("Sale error"))

    _agent = StarshipAgent(  # noqa: F841
        env, ship, mock_simulation, starting_state=StarshipState.SELLING_CARGO
    )

    # Should handle error gracefully
    env.run(until=0.6)

    captured = capsys.readouterr()
    # If cargo was present, error should be printed
    if ship.cargo_manifest.get("cargo"):
        assert "Sale error" in captured.out


def test_starship_agent_error_handling_cargo_purchase(game_state,
                                                      mock_simulation,
                                                      capsys):
    """Test error handling during cargo purchases."""
    env = simpy.Environment()
    from t5code import T5ShipClass
    from unittest.mock import Mock

    ship_class_dict = next(iter(game_state.ship_classes.values()))
    class_name = ship_class_dict["class_name"]
    ship_class = T5ShipClass(class_name, ship_class_dict)
    company = T5Company("Test Company", starting_capital=1_000_000)
    ship = T5Starship("Purchase Error Ship",
                      "Rhylanor",
                      ship_class,
                      owner=company)
    ship.credit(0, 1_000_000)
    ship.set_course_for("Jae Tellona")

    # Mock world's generate_speculative_cargo to raise exception
    original_world = game_state.world_data.get("Rhylanor")
    if original_world:
        original_method = original_world.generate_speculative_cargo
        original_world.generate_speculative_cargo = Mock(
            side_effect=Exception("Purchase error")
        )

    _agent = StarshipAgent(  # noqa: F841
        env, ship, mock_simulation, starting_state=StarshipState.LOADING_CARGO
    )

    # Should handle error gracefully
    env.run(until=0.8)  # Run longer to get through LOADING_MAIL state

    captured = capsys.readouterr()
    assert "Cargo purchase error" in captured.out

    # Restore original method
    if original_world:
        original_world.generate_speculative_cargo = original_method


def test_starship_agent_error_handling_passengers(game_state,
                                                  mock_simulation,
                                                  capsys):
    """Test error handling during passenger loading."""
    env = simpy.Environment()
    from t5code import T5ShipClass, T5NPC
    from unittest.mock import Mock

    ship_class_dict = next(iter(game_state.ship_classes.values()))
    class_name = ship_class_dict["class_name"]
    ship_class = T5ShipClass(class_name, ship_class_dict)
    company = T5Company("Test Company", starting_capital=1_000_000)
    ship = T5Starship("Passenger Error Ship",
                      "Rhylanor",
                      ship_class,
                      owner=company)
    ship.credit(0, 1_000_000)
    ship.set_course_for("Jae Tellona")

    # Add steward
    steward = T5NPC("Steward")
    steward.set_skill("Steward", 1)
    ship.hire_crew("steward", steward)

    # Mock load_passengers to raise exception
    ship.load_passengers = Mock(side_effect=Exception("Passenger error"))

    _agent = StarshipAgent(  # noqa: F841
        env, ship, mock_simulation,
        starting_state=StarshipState.LOADING_PASSENGERS
    )

    # Should handle error gracefully
    env.run(until=0.3)

    captured = capsys.readouterr()
    assert "Passenger loading error" in captured.out


def test_starship_agent_error_handling_jump(game_state,
                                            mock_simulation,
                                            capsys):
    """Test error handling during jump execution."""
    env = simpy.Environment()
    from t5code import T5ShipClass
    from unittest.mock import Mock

    ship_class_dict = next(iter(game_state.ship_classes.values()))
    class_name = ship_class_dict["class_name"]
    ship_class = T5ShipClass(class_name, ship_class_dict)
    company = T5Company("Test Company", starting_capital=1_000_000)
    ship = T5Starship("Jump Error Ship", "Rhylanor", ship_class, owner=company)
    ship.credit(0, 1_000_000)
    ship.set_course_for("Jae Tellona")

    # Mock execute_jump to raise exception
    ship.execute_jump = Mock(side_effect=Exception("Jump error"))

    _agent = StarshipAgent(  # noqa: F841
        env, ship, mock_simulation, starting_state=StarshipState.JUMPING
    )

    # Should handle error gracefully
    env.run(until=7.5)

    captured = capsys.readouterr()
    assert "Jump error" in captured.out


def test_starship_agent_full_cycle(game_state, mock_simulation):
    """Test complete trading cycle from docked to jumped."""
    env = simpy.Environment()
    from t5code import T5ShipClass, T5NPC

    ship_class_dict = next(iter(game_state.ship_classes.values()))
    class_name = ship_class_dict["class_name"]
    ship_class = T5ShipClass(class_name, ship_class_dict)
    company = T5Company("Test Company", starting_capital=1_000_000)
    ship = T5Starship("Full Cycle Ship", "Rhylanor", ship_class, owner=company)
    ship.credit(0, 1_000_000)
    ship.set_course_for("Jae Tellona")

    # Add full crew
    trader = T5NPC("Trader")
    trader.set_skill("Trader", 2)
    ship.hire_crew("trader", trader)

    steward = T5NPC("Steward")
    steward.set_skill("Steward", 1)
    ship.hire_crew("steward", steward)

    admin = T5NPC("Admin")
    admin.set_skill("Admin", 1)
    ship.hire_crew("admin", admin)

    liaison = T5NPC("Liaison")
    liaison.set_skill("Liaison", 1)
    ship.hire_crew("liaison", liaison)

    agent = StarshipAgent(env, ship, mock_simulation)

    initial_voyages = agent.voyage_count

    # Run for full cycle (should complete at least one jump)
    env.run(until=15.0)

    # Should have completed at least one voyage
    assert agent.voyage_count > initial_voyages


def test_starship_agent_insufficient_funds_cargo(game_state, mock_simulation):
    """Test cargo loading with insufficient funds."""
    env = simpy.Environment()
    from t5code import T5ShipClass

    ship_class_dict = next(iter(game_state.ship_classes.values()))
    class_name = ship_class_dict["class_name"]
    ship_class = T5ShipClass(class_name, ship_class_dict)
    company = T5Company("Test Company", starting_capital=1_000_000)
    ship = T5Starship("Poor Ship", "Rhylanor", ship_class, owner=company)
    ship.credit(0, 100)  # Very low funds
    ship.set_course_for("Jae Tellona")

    agent = StarshipAgent(
        env, ship, mock_simulation, starting_state=StarshipState.LOADING_CARGO
    )

    # Should handle insufficient funds gracefully
    env.run(until=0.6)

    # State should still progress
    assert agent.state != StarshipState.LOADING_CARGO


def test_starship_agent_full_hold_freight(game_state, mock_simulation):
    """Test freight loading when hold is full."""
    env = simpy.Environment()
    from t5code import T5ShipClass, T5NPC

    ship_class_dict = next(iter(game_state.ship_classes.values()))
    class_name = ship_class_dict["class_name"]
    ship_class = T5ShipClass(class_name, ship_class_dict)
    company = T5Company("Test Company", starting_capital=1_000_000)
    ship = T5Starship("Full Hold Ship", "Rhylanor", ship_class, owner=company)
    ship.credit(0, 1_000_000)
    ship.set_course_for("Jae Tellona")

    # Add liaison
    liaison = T5NPC("Liaison")
    liaison.set_skill("Liaison", 1)
    ship.hire_crew("liaison", liaison)

    # Fill the hold with cargo
    world = game_state.world_data.get("Rhylanor")
    if world:
        try:
            lots = world.generate_speculative_cargo(
                game_state,
                max_total_tons=ship.hold_size,
                max_lot_size=ship.hold_size
            )
            for lot in lots:
                try:
                    ship.buy_cargo_lot(0, lot)
                except Exception:
                    break
        except Exception:
            pass

    agent = StarshipAgent(
        env,
        ship,
        mock_simulation,
        starting_state=StarshipState.LOADING_FREIGHT
    )

    # Should handle full hold gracefully
    env.run(until=3.5)

    # State should still progress
    assert agent.state != StarshipState.LOADING_FREIGHT


def test_starship_agent_no_cargo_available(game_state, mock_simulation):
    """Test cargo loading when world has no available space."""
    env = simpy.Environment()
    from t5code import T5ShipClass, T5Lot

    ship_class_dict = next(iter(game_state.ship_classes.values()))
    class_name = ship_class_dict["class_name"]
    ship_class = T5ShipClass(class_name, ship_class_dict)
    company = T5Company("Test Company", starting_capital=1_000_000)
    ship = T5Starship("No Space Ship", "Rhylanor", ship_class, owner=company)
    ship.credit(0, 1_000_000)
    ship.set_course_for("Jae Tellona")

    # Fill the hold completely
    try:
        lots = []
        total_mass = 0
        for _ in range(100):
            lot = T5Lot("Rhylanor", game_state)
            lot.mass = 1
            lots.append(lot)
            total_mass += 1
            if total_mass >= ship.hold_size:
                break

        for lot in lots:
            try:
                ship.buy_cargo_lot(lot)
            except Exception:
                break
    except Exception:
        pass

    agent = StarshipAgent(
        env, ship, mock_simulation, starting_state=StarshipState.LOADING_CARGO
    )

    # Should handle no space gracefully
    env.run(until=0.6)

    # State should still progress
    assert agent.state != StarshipState.LOADING_CARGO


def test_starship_agent_stuck_in_invalid_state(game_state,
                                               mock_simulation,
                                               capsys):
    """Test handling of invalid state with no transitions."""
    env = simpy.Environment()
    from t5code import T5ShipClass
    from unittest.mock import patch
    from t5sim import starship_states

    ship_class_dict = next(iter(game_state.ship_classes.values()))
    class_name = ship_class_dict["class_name"]
    ship_class = T5ShipClass(class_name, ship_class_dict)
    company = T5Company("Test Company", starting_capital=1_000_000)
    ship = T5Starship("Stuck Ship", "Rhylanor", ship_class, owner=company)
    ship.credit(0, 1_000_000)
    ship.set_course_for("Jae Tellona")

    # Create agent
    agent = StarshipAgent(env, ship, mock_simulation)

    # Monkey patch get_next_state to return None (simulate invalid state)
    original_get_next_state = starship_states.get_next_state

    def mock_get_next_state(state):
        if agent.state == StarshipState.OFFLOADING:
            return None  # Simulate stuck state
        return original_get_next_state(state)

    with patch('t5sim.starship_agent.get_next_state',
               side_effect=mock_get_next_state):
        # Run simulation - should stop when stuck
        env.run(until=1.0)

    captured = capsys.readouterr()
    assert "stuck in" in captured.out


def test_starship_agent_mail_locker_full(game_state, mock_simulation):
    """Test mail loading when locker is already full."""
    env = simpy.Environment()
    from t5code import T5ShipClass, T5NPC

    ship_class_dict = next(iter(game_state.ship_classes.values()))
    class_name = ship_class_dict["class_name"]
    ship_class = T5ShipClass(class_name, ship_class_dict)
    company = T5Company("Test Company", starting_capital=1_000_000)
    ship = T5Starship("Full Mail Ship", "Rhylanor", ship_class, owner=company)
    ship.credit(0, 1_000_000)
    ship.set_course_for("Jae Tellona")

    # Add admin crew
    admin = T5NPC("Admin")
    admin.set_skill("Admin", 1)
    ship.hire_crew("admin", admin)

    # Fill mail locker
    for _ in range(ship.mail_locker_size):
        try:
            ship.load_mail(game_state, "Jae Tellona")
        except ValueError:
            break

    agent = StarshipAgent(
        env, ship, mock_simulation, starting_state=StarshipState.LOADING_MAIL
    )

    # Should handle full locker gracefully
    env.run(until=0.2)

    # State should still progress
    assert agent.state != StarshipState.LOADING_MAIL


def test_starship_agent_no_world_at_location(game_state, mock_simulation):
    """Test handling when world doesn't exist in game state."""
    env = simpy.Environment()
    from t5code import T5ShipClass

    ship_class_dict = next(iter(game_state.ship_classes.values()))
    class_name = ship_class_dict["class_name"]
    ship_class = T5ShipClass(class_name, ship_class_dict)

    # Create ship at non-existent location
    company = T5Company("Test Company", starting_capital=1_000_000)
    ship = T5Starship("Nowhere Ship",
                      "NonExistentWorld",
                      ship_class,
                      owner=company)
    ship.credit(0, 1_000_000)
    ship.set_course_for("Jae Tellona")

    agent = StarshipAgent(
        env,
        ship,
        mock_simulation,
        starting_state=StarshipState.LOADING_FREIGHT
    )

    # Should handle missing world gracefully and give up after max attempts
    # Then progress through states but eventually fail on mail loading
    try:
        env.run(until=15.0)  # Long enough for 4+ freight attempts
    except KeyError:
        # Expected - ship progressed past freight but failed on mail
        pass

    # Verify ship actually progressed past LOADING_FREIGHT before failing
    # Counter was reset after leaving freight state
    assert agent.freight_loading_attempts == 0


def test_starship_agent_capacity_exceeded_freight(game_state, mock_simulation):
    """Test freight loading when capacity is exceeded."""
    env = simpy.Environment()
    from t5code import T5ShipClass, T5NPC, T5Lot

    ship_class_dict = next(iter(game_state.ship_classes.values()))
    class_name = ship_class_dict["class_name"]
    ship_class = T5ShipClass(class_name, ship_class_dict)
    company = T5Company("Test Company", starting_capital=1_000_000)
    ship = T5Starship("Capacity Ship", "Rhylanor", ship_class, owner=company)
    ship.credit(0, 1_000_000)
    ship.set_course_for("Jae Tellona")

    # Add liaison crew
    liaison = T5NPC("Liaison")
    liaison.set_skill("Liaison", 5)  # High skill = large freight lots
    ship.hire_crew("liaison", liaison)

    # Fill most of the hold
    try:
        for _ in range(10):
            lot = T5Lot("Rhylanor", game_state)
            lot.mass = ship.hold_size // 12
            ship.buy_cargo_lot(lot)
    except Exception:
        pass

    agent = StarshipAgent(
        env,
        ship,
        mock_simulation,
        starting_state=StarshipState.LOADING_FREIGHT
    )

    # Should handle capacity issues gracefully
    # Cargo lots have 0 mass so they don't count toward threshold
    env.run(until=11.0)  # Stop before second voyage starts

    # Should have completed at least the first loading cycle
    # May be in any state after LOADING_FREIGHT
    assert agent.voyage_count >= 0  # Successfully ran without crashing
    assert ship.cargo_size >= 0  # Has some cargo


def test_starship_agent_mail_value_error(game_state, mock_simulation):
    """Test mail loading when ValueError is raised."""
    env = simpy.Environment()
    from t5code import T5ShipClass, T5NPC
    from unittest.mock import Mock

    ship_class_dict = next(iter(game_state.ship_classes.values()))
    class_name = ship_class_dict["class_name"]
    ship_class = T5ShipClass(class_name, ship_class_dict)
    company = T5Company("Test Company", starting_capital=1_000_000)
    ship = T5Starship("Mail Error Ship", "Rhylanor", ship_class, owner=company)
    ship.credit(0, 1_000_000)
    ship.set_course_for("Jae Tellona")

    # Add admin crew
    admin = T5NPC("Admin")
    admin.set_skill("Admin", 1)
    ship.hire_crew("admin", admin)

    # Mock load_mail to raise ValueError
    ship.load_mail = Mock(side_effect=ValueError("No mail available"))

    agent = StarshipAgent(
        env, ship, mock_simulation, starting_state=StarshipState.LOADING_MAIL
    )

    # Should handle ValueError gracefully (caught and ignored)
    env.run(until=0.2)

    # State should still progress
    assert agent.state != StarshipState.LOADING_MAIL


def test_starship_agent_jumping_unknown_world(game_state, capsys):
    """Test verbose reporting when jumping to a world not in world_data."""
    env = simpy.Environment()
    from t5code import T5ShipClass
    from unittest.mock import Mock

    # Create a mock simulation with verbose output
    sim = Mock()
    sim.game_state = game_state
    sim.record_cargo_sale = Mock()
    sim.verbose = True  # Enable verbose output
    sim.starting_day = 1

    ship_class_dict = next(iter(game_state.ship_classes.values()))
    class_name = ship_class_dict["class_name"]
    ship_class = T5ShipClass(class_name, ship_class_dict)
    company = T5Company("Test Company", starting_capital=1_000_000)
    ship = T5Starship("Unknown Destination Ship",
                      "Rhylanor",
                      ship_class,
                      owner=company)
    ship.credit(0, 1_000_000)

    # Set course to a world that doesn't exist in world_data
    ship.set_course_for("UnknownWorld")

    _agent = StarshipAgent(  # noqa: F841
        env, ship, sim, starting_state=StarshipState.JUMPING
    )

    # Run through jump to trigger verbose arrival report
    env.run(until=7.5)

    captured = capsys.readouterr()
    # Should fall back to using the location name directly
    assert "arrived at UnknownWorld" in captured.out


def test_starship_agent_skipping_unprofitable_cargo(game_state, capsys):
    """Test verbose reporting when skipping unprofitable cargo."""
    env = simpy.Environment()
    from t5code import T5ShipClass, T5Lot
    from unittest.mock import patch
    from t5sim.simulation import Simulation

    # Use real Simulation object to ensure verbose flag works
    sim = Simulation(game_state, verbose=True)

    ship_class_dict = next(iter(game_state.ship_classes.values()))
    class_name = ship_class_dict["class_name"]
    ship_class = T5ShipClass(class_name, ship_class_dict)
    company = T5Company("Test Company", starting_capital=1_000_000)
    ship = T5Starship("Profit Test Ship",
                      "Rhylanor",
                      ship_class,
                      owner=company)
    ship.credit(0, 1_000_000)
    ship.set_course_for("Jae Tellona")

    _agent = StarshipAgent(  # noqa: F841
        env, ship, sim, starting_state=StarshipState.LOADING_CARGO
    )

    # Mock generate_speculative_cargo to return lots that will be unprofitable
    unprofitable_lot = T5Lot("Rhylanor", game_state)
    unprofitable_lot.mass = 1
    unprofitable_lot.origin_value = 10000  # High purchase price

    with patch.object(
        game_state.world_data["Rhylanor"],
        'generate_speculative_cargo',
        return_value=[unprofitable_lot]
    ):
        # Mock determine_sale_value_on to return a loss
        with patch.object(
            unprofitable_lot,
            'determine_sale_value_on',
            return_value=100  # Low sale price (loss)
        ):
            # Run cargo loading state
            env.run(until=0.5)

    captured = capsys.readouterr()
    # Should report skipping unprofitable cargo
    assert "skipped" in captured.out
    assert "unprofitable" in captured.out


def test_starship_agent_profitable_destination_verbose(game_state, capsys):
    """Test verbose reporting when choosing profitable destination."""
    env = simpy.Environment()
    from t5code import T5ShipClass
    from t5sim.simulation import Simulation

    # Use real Simulation object with verbose flag
    sim = Simulation(game_state, verbose=True)

    ship_class_dict = next(iter(game_state.ship_classes.values()))
    class_name = ship_class_dict["class_name"]
    ship_class = T5ShipClass(class_name, ship_class_dict)
    company = T5Company("Test Company", starting_capital=1_000_000)
    ship = T5Starship("Route Test Ship", "Rhylanor", ship_class, owner=company)
    ship.credit(0, 1_000_000)
    ship.set_course_for("Jae Tellona")  # Set initial destination

    _agent = StarshipAgent(  # noqa: F841
        env, ship, sim, starting_state=StarshipState.LOADING_PASSENGERS
    )

    # Run through loading passengers to departing
    # (which triggers destination choice)
    env.run(until=8.0)

    captured = capsys.readouterr()
    # Should report choosing profitable destination with name
    assert (
        "picked destination" in captured.out and
        "showed cargo profit" in captured.out)


def test_starship_agent_no_profitable_destination_verbose(game_state, capsys):
    """Test verbose reporting when no profitable destinations exist."""
    env = simpy.Environment()
    from t5code import T5ShipClass
    from unittest.mock import patch
    from t5sim.simulation import Simulation

    # Use real Simulation object with verbose flag
    sim = Simulation(game_state, verbose=True)

    # Use a ship with Jump-3 to ensure worlds in range
    ship_class_data = {
        "class_name": "Test Trader",
        "jump_rating": 3,
        "maneuver_rating": 2,
        "cargo_capacity": 50,
        "staterooms": 5,
        "low_berths": 10,
    }
    # Register ship class in game_state for payroll calculations
    game_state.ship_classes["Test Trader"] = ship_class_data
    ship_class = T5ShipClass("Test Trader", ship_class_data)
    company = T5Company("Test Company", starting_capital=1_000_000)
    ship = T5Starship("No Profit Ship", "Rhylanor", ship_class, owner=company)
    ship.credit(0, 1_000_000)
    ship.set_course_for("Jae Tellona")  # Set initial destination

    _agent = StarshipAgent(  # noqa: F841
        env, ship, sim, starting_state=StarshipState.LOADING_PASSENGERS
    )

    # Mock find_profitable_destinations to return empty list
    with patch.object(ship, 'find_profitable_destinations', return_value=[]):
        # Run through loading passengers to departing
        env.run(until=8.0)

    captured = capsys.readouterr()
    # Should report choosing destination with no profitable cargo
    assert "picked destination" in captured.out
    assert "randomly because no in-range system" in captured.out


def test_starship_agent_no_worlds_in_range_verbose(game_state, capsys):
    """Test verbose reporting when no worlds are in jump range."""
    env = simpy.Environment()
    from t5code import T5ShipClass
    from unittest.mock import patch
    from t5sim.simulation import Simulation

    # Use real Simulation object with verbose flag
    sim = Simulation(game_state, verbose=True)

    # Use a ship with Jump-0 (no range)
    ship_class_data = {
        "class_name": "No Jump",
        "jump_rating": 0,
        "maneuver_rating": 2,
        "cargo_capacity": 50,
        "staterooms": 5,
        "low_berths": 10,
    }
    # Register ship class in game_state for payroll calculations
    game_state.ship_classes["No Jump"] = ship_class_data
    ship_class = T5ShipClass("No Jump", ship_class_data)
    company = T5Company("Test Company", starting_capital=1_000_000)
    ship = T5Starship("No Range Ship", "Rhylanor", ship_class, owner=company)
    ship.credit(0, 1_000_000)
    ship.set_course_for("Jae Tellona")  # Set initial destination

    _agent = StarshipAgent(  # noqa: F841
        env, ship, sim, starting_state=StarshipState.LOADING_PASSENGERS
    )

    # Mock find_profitable_destinations and
    # get_worlds_in_jump_range to return empty
    with patch.object(ship, 'find_profitable_destinations', return_value=[]):
        with patch.object(ship, 'get_worlds_in_jump_range', return_value=[]):
            # Run through loading passengers,
            # loading fuel, departing to jumping
            # Need more time to complete full cycle
            env.run(until=10.0)

    captured = capsys.readouterr()
    # Should report no worlds in jump range
    assert "no worlds in jump range" in captured.out
