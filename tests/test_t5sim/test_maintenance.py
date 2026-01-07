"""Tests for annual maintenance scheduling and execution."""

from t5code import T5Company, T5NPC, T5ShipClass, T5Starship
from t5sim.starship_states import StarshipState


def test_ship_has_maintenance_attributes(test_ship_data):
    """Test that ships have maintenance tracking attributes."""
    ship_class_data = test_ship_data["small"]
    ship_class = T5ShipClass("small", ship_class_data)
    company = T5Company("Test Company", starting_capital=1000000)
    ship = T5Starship("Test Ship", "Rhylanor", ship_class, company)

    assert hasattr(ship, 'annual_maintenance_day')
    assert hasattr(ship, 'needs_maintenance')
    assert hasattr(ship, 'last_maintenance_year')
    assert isinstance(ship.annual_maintenance_day, int)
    assert 2 <= ship.annual_maintenance_day <= 365
    assert ship.needs_maintenance is False
    assert ship.last_maintenance_year == 1104


def test_maintenance_day_boundary_conditions(test_ship_data):
    """Test edge cases for maintenance day values."""
    ship_class_data = test_ship_data["small"]
    ship_class = T5ShipClass("small", ship_class_data)
    company = T5Company("Test Company", starting_capital=1000000)

    # Create many ships and check their maintenance days
    for i in range(100):
        ship = T5Starship(f"Ship {i}", "Rhylanor", ship_class, company)
        assert 2 <= ship.annual_maintenance_day <= 365
        assert ship.annual_maintenance_day != 1  # Never on holiday


def test_maintenance_flag_can_be_set(test_ship_data):
    """Test that maintenance flag can be set and cleared."""
    ship_class_data = test_ship_data["small"]
    ship_class = T5ShipClass("small", ship_class_data)
    company = T5Company("Test Company", starting_capital=1000000)
    ship = T5Starship("Test Ship", "Rhylanor", ship_class, company)

    # Initially should not need maintenance
    assert ship.needs_maintenance is False

    # Can set flag
    ship.needs_maintenance = True
    assert ship.needs_maintenance is True
    # Can clear flag
    ship.needs_maintenance = False
    assert ship.needs_maintenance is False


def test_maintenance_year_tracking(test_ship_data):
    """Test that last maintenance year can be tracked."""
    ship_class_data = test_ship_data["small"]
    ship_class = T5ShipClass("small", ship_class_data)
    company = T5Company("Test Company", starting_capital=1000000)
    ship = T5Starship("Test Ship", "Rhylanor", ship_class, company)

    # Initially set to 1104 (default simulation year, maintenance current)
    assert ship.last_maintenance_year == 1104

    # Can update to a different year
    ship.last_maintenance_year = 1106
    assert ship.last_maintenance_year == 1106


def test_different_ships_have_different_maintenance_days(test_ship_data):
    """Test that different ships get different
    maintenance days (probabilistic)."""
    ship_class_data = test_ship_data["small"]
    ship_class = T5ShipClass("small", ship_class_data)
    company = T5Company("Test Company", starting_capital=1000000)

    maintenance_days = set()
    for i in range(50):
        ship = T5Starship(f"Ship {i}", "Rhylanor", ship_class, company)
        maintenance_days.add(ship.annual_maintenance_day)

    # With 50 ships, should have multiple different days
    assert len(maintenance_days) > 1


def test_large_ships_also_get_maintenance_days(test_ship_data):
    """Test that all ship types get maintenance days."""
    for ship_type in ["small", "large"]:
        ship_class_data = test_ship_data[ship_type]
        ship_class = T5ShipClass(ship_type, ship_class_data)
        company = T5Company("Test Company", starting_capital=1000000)
        ship = T5Starship(f"{ship_type} Ship", "Rhylanor", ship_class, company)

        assert hasattr(ship, 'annual_maintenance_day')
        assert 2 <= ship.annual_maintenance_day <= 365
        assert hasattr(ship, 'needs_maintenance')
        assert hasattr(ship, 'last_maintenance_year')


def test_maintenance_state_exists_in_enum():
    """Test that MAINTENANCE state exists in StarshipState enum."""
    assert hasattr(StarshipState, 'MAINTENANCE')
    assert StarshipState.MAINTENANCE is not None


def test_maintenance_attributes_persist(test_ship_data):
    """Test that maintenance attributes don't change unexpectedly."""
    ship_class_data = test_ship_data["small"]
    ship_class = T5ShipClass("small", ship_class_data)
    company = T5Company("Test Company", starting_capital=1000000)
    ship = T5Starship("Test Ship", "Rhylanor", ship_class, company)

    original_day = ship.annual_maintenance_day
    original_needs = ship.needs_maintenance
    original_year = ship.last_maintenance_year

    # Do some ship operations
    ship.set_course_for("Jae Tellona")
    pilot = T5NPC("Pilot")
    pilot.set_skill("Pilot", 2)
    ship.hire_crew("pilot", pilot)

    # Attributes should still be the same
    assert ship.annual_maintenance_day == original_day
    assert ship.needs_maintenance == original_needs
    assert ship.last_maintenance_year == original_year


def test_maintenance_transition_after_offloading(setup_test_gamestate):
    """Test that ship transitions to MAINTENANCE state when needed."""
    import simpy
    from t5sim.starship_agent import StarshipAgent
    from t5sim.simulation import Simulation
    from t5code import T5Company, T5ShipClass, T5Starship

    # Create simulation
    env = simpy.Environment()
    simulation = Simulation(
        setup_test_gamestate, num_ships=1, starting_day=15, starting_year=1105
    )

    # Create ship with specific maintenance day
    ship_class_data = simulation.game_state.ship_classes.get("small")
    ship_class = T5ShipClass("small", ship_class_data)
    company = T5Company("Test Company", starting_capital=1000000)
    ship = T5Starship("Test Scout", "Rhylanor", ship_class, company)

    # Set up for maintenance: past maintenance day, not done this year
    ship.annual_maintenance_day = 10  # Early in the year
    ship.last_maintenance_year = 1104  # Last year
    ship.needs_maintenance = False

    # Create agent in SELLING_CARGO state at day 15 (past maintenance day)
    agent = StarshipAgent(
        env, ship, simulation, starting_state=StarshipState.SELLING_CARGO
    )

    # Run just the state transition after selling cargo
    agent._check_if_maintenance_needed()

    # Should now need maintenance
    assert ship.needs_maintenance is True

    # Transition should move to MAINTENANCE state
    result = agent._transition_to_next_state()
    assert result is True
    assert agent.state == StarshipState.MAINTENANCE


def test_day_of_year_edge_case_over_365(setup_test_gamestate):
    """Test edge case where calculated day exceeds 365."""
    import simpy
    from t5sim.starship_agent import StarshipAgent
    from t5sim.simulation import Simulation
    from t5code import T5Company, T5ShipClass, T5Starship

    # Create simulation starting very late in the year
    env = simpy.Environment()
    simulation = Simulation(setup_test_gamestate,
                            num_ships=1,
                            starting_day=364)

    # Create ship
    ship_class_data = simulation.game_state.ship_classes.get("small")
    ship_class = T5ShipClass("small", ship_class_data)
    company = T5Company("Test Company", starting_capital=1000000)
    ship = T5Starship("Test Scout", "Rhylanor", ship_class, company)

    # Set maintenance day near end of year
    ship.annual_maintenance_day = 364
    ship.last_maintenance_year = 1104

    agent = StarshipAgent(
        env, ship, simulation, starting_state=StarshipState.DOCKED
    )

    # Manually set env.now to a value that would cause day > 365
    # This is an edge case that shouldn't normally
    # happen but the code defends against it
    env._now = 730  # 2 years worth of days

    # Check maintenance - this will exercise the day > 365 clamp
    agent._check_if_maintenance_needed()

    # The function should complete without error
    # and should have clamped day_of_year to 365

    # Because we're past the maintenance day
    assert ship.needs_maintenance is True


def test_maintenance_insufficient_funds_marks_broke(
        setup_test_gamestate, test_ship_data):
    """Test that ship becomes broke if it can't afford maintenance."""
    import simpy
    from t5sim.starship_agent import StarshipAgent
    from t5sim.simulation import Simulation
    from t5code import T5Company, T5ShipClass, T5Starship

    env = simpy.Environment()
    simulation = Simulation(setup_test_gamestate,
                            num_ships=1,
                            starting_day=100,
                            starting_year=1105)

    # Create ship with known cost
    ship_class_data = test_ship_data["small"]
    ship_class = T5ShipClass("small", ship_class_data)
    company = T5Company("Broke Company", starting_capital=100)
    ship = T5Starship("Broke Ship", "Rhylanor", ship_class, company)

    # Set maintenance day to trigger immediately
    ship.annual_maintenance_day = 100
    ship.last_maintenance_year = 1104  # Last year
    ship.needs_maintenance = True

    # Set balance to less than maintenance cost
    # Maintenance = ship_cost * 1000
    # small ship costs MCr 28.57, so maintenance = Cr 28,570
    ship.owner.cash.post(time=0, amount=-ship.owner.balance + 500,
                         memo="Test: reduce to 500")

    agent = StarshipAgent(
        env, ship, simulation, starting_state=StarshipState.MAINTENANCE
    )

    # Capture the starting balance
    starting_balance = ship.owner.balance
    assert starting_balance == 500

    # Run simulation to trigger maintenance
    env.run(until=1.0)

    # Ship should be marked as broke
    assert agent.broke is True

    # Balance should not have changed (maintenance not charged)
    assert ship.owner.balance == starting_balance


def test_maintenance_charges_correct_amount(
        setup_test_gamestate, test_ship_data):
    """Test that maintenance charges 1/1000th of ship cost."""
    import simpy
    from t5sim.starship_agent import StarshipAgent
    from t5sim.simulation import Simulation
    from t5code import T5Company, T5ShipClass, T5Starship

    env = simpy.Environment()
    simulation = Simulation(setup_test_gamestate,
                            num_ships=1,
                            starting_day=100,
                            starting_year=1105)

    # Create ship with known cost
    ship_class_data = test_ship_data["small"]
    ship_class = T5ShipClass("small", ship_class_data)
    company = T5Company("Rich Company", starting_capital=1000000)
    ship = T5Starship("Test Ship", "Rhylanor", ship_class, company)

    # Set maintenance day to trigger immediately
    ship.annual_maintenance_day = 100
    ship.last_maintenance_year = 1104  # Last year
    ship.needs_maintenance = True

    # Capture the starting balance
    starting_balance = ship.owner.balance

    agent = StarshipAgent(
        env, ship, simulation, starting_state=StarshipState.MAINTENANCE
    )

    # Run simulation to trigger maintenance
    env.run(until=1.0)

    # Ship should not be broke
    assert agent.broke is False

    # Calculate expected maintenance cost
    # small ship costs MCr 28.57, so maintenance = Cr 28,570
    ship_cost_mcr = ship_class_data.get("ship_cost", 0.0)
    expected_cost = int(ship_cost_mcr * 1000)

    # Balance should have been reduced by maintenance cost
    assert ship.owner.balance == starting_balance - expected_cost

    # Maintenance should be marked as complete
    assert ship.needs_maintenance is False
    assert ship.last_maintenance_year == 1105


def test_annual_profit_and_crew_share(setup_test_gamestate, capsys):
    """Test that annual profit is calculated and crew gets 10% share."""
    import simpy
    from t5sim.starship_agent import StarshipAgent
    from t5sim.simulation import Simulation
    from t5code import T5Company, T5ShipClass, T5Starship

    # Create simulation starting at beginning of year
    env = simpy.Environment()
    simulation = Simulation(
        setup_test_gamestate,
        num_ships=1,
        starting_day=10,
        starting_year=1105,
        verbose=True
    )

    # Create ship
    ship_class_data = simulation.game_state.ship_classes.get("small")
    ship_class = T5ShipClass("small", ship_class_data)
    company = T5Company("Test Company", starting_capital=1000000)
    ship = T5Starship("Profit Ship", "Rhylanor", ship_class, company)

    # Set maintenance day and tracking
    ship.annual_maintenance_day = 15
    ship.last_maintenance_year = 1104  # Last year
    ship.needs_maintenance = False

    agent = StarshipAgent(
        env, ship, simulation, starting_state=StarshipState.DOCKED
    )

    # Simulate profitable trading by crediting the ship
    ship.credit(0, 50000, "Simulated profit")
    assert ship.owner.balance == 1050000

    # Jump clock forward past maintenance day (to day 380 of simulation)
    env._now = 370

    # Trigger maintenance check
    agent._check_if_maintenance_needed()
    assert ship.needs_maintenance is True

    # Perform maintenance - this should report profit and pay crew share
    agent._perform_maintenance()

    # Capture output
    captured = capsys.readouterr()

    # Verify profit was reported
    assert "annual profit: Cr50,000" in captured.out
    assert "1,000,000 to Cr1,050,000" in captured.out

    # Verify crew share was paid (10% of 50,000 = 5,000)
    assert "crew profit share: Cr5,000" in captured.out
    assert "10% of annual profit" in captured.out

    # Verify maintenance was paid
    ship_cost_mcr = ship_class_data.get("ship_cost", 0.0)
    expected_maintenance = int(ship_cost_mcr * 1000)
    expected_crew_share = 5000

    # Balance should be: 1,050,000 - 5,000 (crew) - maintenance
    expected_balance = 1050000 - expected_crew_share - expected_maintenance
    assert ship.owner.balance == expected_balance

    # Verify last_year_balance was updated
    assert agent.last_year_balance == expected_balance
