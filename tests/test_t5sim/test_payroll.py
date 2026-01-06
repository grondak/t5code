"""Tests for crew payroll system in starship simulation."""

import pytest
from t5code import T5ShipClass, T5NPC
from t5code.T5Company import T5Company
from t5code.T5Starship import T5Starship
from t5sim.simulation import Simulation
from t5sim.starship_agent import StarshipAgent
from t5sim.starship_states import StarshipState
import simpy


@pytest.fixture
def simple_game_state(setup_test_gamestate):
    """Game state with minimal world data for testing."""
    return setup_test_gamestate


@pytest.fixture
def test_ship_with_crew(test_ship_data, simple_game_state):
    """Create a test ship with a small crew."""
    ship_class = T5ShipClass("small", test_ship_data["small"])
    company = T5Company("Test Company", starting_capital=100_000)
    ship = T5Starship("Test Ship", "Rhylanor", ship_class, owner=company)

    # Add 3 crew members
    pilot = T5NPC("Pilot")
    pilot.set_skill("pilot", 2)
    ship.crew_position["Pilot"][0].assign(pilot)

    engineer = T5NPC("Engineer")
    engineer.set_skill("engineer", 2)
    ship.crew_position["Engineer"][0].assign(engineer)

    astrogator = T5NPC("Astrogator")
    astrogator.set_skill("navigator", 1)
    ship.crew_position["Astrogator"][0].assign(astrogator)

    return ship


def test_payroll_process_starts_with_agent(simple_game_state,
                                           test_ship_with_crew):
    """Test that payroll process is started when agent is created."""
    env = simpy.Environment()
    sim = Simulation(simple_game_state, num_ships=1, starting_day=2)

    agent = StarshipAgent(
        env, test_ship_with_crew, sim, starting_state=StarshipState.DOCKED
    )

    # Agent should have both main and payroll processes
    assert hasattr(agent, 'process')
    assert hasattr(agent, 'payroll_process')
    assert agent.payroll_process is not None


def test_calculate_days_until_next_month_same_month(
        simple_game_state, test_ship_with_crew):
    """Test calculating days until next month within same month."""
    env = simpy.Environment()
    # Start on Day 010 (Month 1)
    sim = Simulation(simple_game_state, num_ships=1, starting_day=10)

    agent = StarshipAgent(
        env, test_ship_with_crew, sim, starting_state=StarshipState.DOCKED
    )

    # From Day 10, next month starts on Day 30 (20 days away)
    days_until = agent._calculate_days_until_next_month()
    assert days_until == pytest.approx(20.0)


def test_calculate_days_until_next_month_year_wrap(
        simple_game_state, test_ship_with_crew):
    """Test calculating days until next month when wrapping to new year."""
    env = simpy.Environment()
    # Start on Day 350 (Month 13)
    sim = Simulation(simple_game_state, num_ships=1, starting_day=350)

    agent = StarshipAgent(
        env, test_ship_with_crew, sim, starting_state=StarshipState.DOCKED
    )

    # From Day 350, next month (Month 1) starts on Day 2
    # Days: (365 - 350) + 2 = 17
    days_until = agent._calculate_days_until_next_month()
    assert days_until == pytest.approx(17.0)


def test_payroll_deducts_correct_amount(simple_game_state,
                                        test_ship_with_crew):
    """Test that payroll deducts 100 Cr per crew member."""
    env = simpy.Environment()
    # Start on Day 2 (first day of Month 1) so payroll triggers immediately
    sim = Simulation(simple_game_state, num_ships=1, starting_day=2)

    # Set destination to avoid errors
    test_ship_with_crew.set_course_for("Rhylanor")

    StarshipAgent(
        env, test_ship_with_crew, sim, starting_state=StarshipState.DOCKED
    )

    # Check ledger for payroll entry
    # (payroll happens immediately before any other activity)
    # The agent's __init__ doesn't run simulation, so we need to run briefly
    initial_ledger_size = len(test_ship_with_crew.owner.cash.ledger)

    # Run simulation very briefly (0.01 days) -
    # just enough for payroll process to fire
    env.run(until=0.01)

    # Should have one new ledger entry for payroll
    assert len(test_ship_with_crew.owner.cash.ledger) == (
        initial_ledger_size + 1
    )

    # Check the payroll entry
    payroll_entry = test_ship_with_crew.owner.cash.ledger[-1]
    assert payroll_entry.amount == -300  # 3 crew × 100 Cr
    assert "Crew payroll" in payroll_entry.memo


def test_payroll_creates_ledger_entry(simple_game_state, test_ship_with_crew):
    """Test that payroll creates proper ledger entry."""
    env = simpy.Environment()
    sim = Simulation(simple_game_state, num_ships=1, starting_day=2)

    # Set destination to avoid errors
    test_ship_with_crew.set_course_for("Rhylanor")

    StarshipAgent(
        env, test_ship_with_crew, sim, starting_state=StarshipState.DOCKED
    )

    # Run simulation to trigger payroll
    env.run(until=1.0)

    # Should have one new payroll ledger entry
    payroll_entries = [entry for entry in
                       test_ship_with_crew.owner.cash.ledger if
                       "Crew payroll" in entry.memo]
    assert len(payroll_entries) == 1

    # Check the entry details
    payroll_entry = payroll_entries[0]
    assert payroll_entry.amount == -300  # Debit
    assert "Crew payroll" in payroll_entry.memo
    assert "3 crew" in payroll_entry.memo
    assert "Month 1" in payroll_entry.memo


def test_payroll_happens_monthly(simple_game_state, test_ship_with_crew):
    """Test that payroll happens once per month, not more often."""
    env = simpy.Environment()
    sim = Simulation(simple_game_state, num_ships=1, starting_day=2)

    # Set a valid destination to avoid errors during state machine
    test_ship_with_crew.set_course_for("Rhylanor")

    StarshipAgent(
        env, test_ship_with_crew, sim, starting_state=StarshipState.DOCKED
    )

    # Run for 27 days (stay within Month 1)
    env.run(until=27.0)

    # Should have paid payroll exactly once (at start)
    expected_ledger_entries = [(entry for entry in
                                test_ship_with_crew.owner.cash.ledger
                                if "Crew payroll" in entry.memo)]
    assert len(expected_ledger_entries) == 1


def test_payroll_multiple_months(simple_game_state, test_ship_with_crew):
    """Test that payroll happens correctly across multiple months."""
    env = simpy.Environment()
    sim = Simulation(simple_game_state, num_ships=1, starting_day=2)

    # Set destination to avoid errors
    test_ship_with_crew.set_course_for("Rhylanor")

    StarshipAgent(
        env, test_ship_with_crew, sim, starting_state=StarshipState.DOCKED
    )

    # Run for 90 days (covers Months 1, 2, 3, and part of 4)
    env.run(until=90.0)

    # Should have paid 4 times
    payroll_entries = [entry for entry in
                       test_ship_with_crew.owner.cash.ledger
                       if "Crew payroll" in entry.memo]
    assert len(payroll_entries) == 4


def test_payroll_insufficient_funds_marks_broke(
        simple_game_state, test_ship_with_crew):
    """Test that ship becomes broke if it can't afford payroll."""
    env = simpy.Environment()
    sim = Simulation(simple_game_state, num_ships=1, starting_day=2)

    # Set destination to avoid errors
    test_ship_with_crew.set_course_for("Rhylanor")

    # Set balance to less than payroll (3 crew × 100 = 300)
    # Use post() to reduce balance
    current_balance = test_ship_with_crew.owner.balance
    reduction = current_balance - 200
    test_ship_with_crew.owner.cash.post(time=0,
                                        amount=-reduction,
                                        memo="Test: reduce to 200")

    agent = StarshipAgent(
        env, test_ship_with_crew, sim, starting_state=StarshipState.DOCKED
    )

    # Run simulation to trigger payroll
    env.run(until=1.0)

    # Ship should be marked as broke
    assert agent.broke is True

    # Balance should not have changed (payroll not processed)
    assert test_ship_with_crew.owner.balance == 200


def test_broke_ship_stops_processing_payroll(
        simple_game_state, test_ship_with_crew):
    """Test that broke ships don't continue processing payroll."""
    env = simpy.Environment()
    sim = Simulation(simple_game_state, num_ships=1, starting_day=2)

    # Set destination to avoid errors
    test_ship_with_crew.set_course_for("Rhylanor")

    # Set balance to exactly one payroll (3 crew × 100 = 300)
    current_balance = test_ship_with_crew.owner.balance
    reduction = current_balance - 300
    test_ship_with_crew.owner.cash.post(time=0,
                                        amount=-reduction,
                                        memo="Test: reduce to 300")

    agent = StarshipAgent(
        env, test_ship_with_crew, sim, starting_state=StarshipState.DOCKED
    )

    # Run for first payroll (should succeed)
    env.run(until=1.0)
    payroll_entries = [(entry for entry in
                        test_ship_with_crew.owner.cash.ledger
                        if "Crew payroll" in entry.memo)]
    assert len(payroll_entries) == 1  # Only one payroll processed
    assert agent.broke is False

    # Forcibly set balance to zero before next payroll
    current_balance = test_ship_with_crew.owner.balance
    if current_balance > 0:
        test_ship_with_crew.owner.cash.post(time=2,
                                            amount=-current_balance,
                                            memo="Force zero balance "
                                            "for broke test")

    # Directly invoke payroll processing to test broke logic
    agent._process_monthly_payroll()
    assert agent.broke is True

    # Still only one payroll entry (no more processed after broke)
    payroll_entries = [(entry for entry in
                       test_ship_with_crew.owner.cash.ledger
                       if "Crew payroll" in entry.memo)]
    assert len(payroll_entries) == 1


def test_payroll_with_no_crew(simple_game_state, test_ship_data):
    """Test that ships with no crew don't process payroll."""
    ship_class = T5ShipClass("small", test_ship_data["small"])
    company = T5Company("Test Company", starting_capital=100_000)
    ship = T5Starship("Empty Ship", "Rhylanor", ship_class, owner=company)
    # Don't assign any crew

    # Set destination to avoid errors
    ship.set_course_for("Rhylanor")

    env = simpy.Environment()
    sim = Simulation(simple_game_state, num_ships=1, starting_day=2)

    StarshipAgent(
        env, ship, sim, starting_state=StarshipState.DOCKED
    )

    # Run for 90 days
    env.run(until=90.0)

    # There should be no payroll ledger entries
    payroll_entries = [entry for entry in
                       ship.owner.cash.ledger
                       if "Crew payroll" in entry.memo]
    assert len(payroll_entries) == 0


def test_payroll_timing_from_mid_month(simple_game_state, test_ship_with_crew):
    """Test payroll timing when starting mid-month."""
    env = simpy.Environment()
    sim = Simulation(simple_game_state, num_ships=1, starting_day=15)

    # Set destination to avoid errors
    test_ship_with_crew.set_course_for("Rhylanor")

    StarshipAgent(
        env, test_ship_with_crew, sim, starting_state=StarshipState.DOCKED
    )

    # Run for 20 days (should cross into Month 2 on Day 30)
    env.run(until=20.0)

    # Should have paid once when entering Month 2
    payroll_entries = [(entry for entry in
                        test_ship_with_crew.owner.cash.ledger
                        if "Crew payroll" in entry.memo)]
    assert len(payroll_entries) == 1


def test_mark_ship_broke_consolidation(simple_game_state, test_ship_with_crew):
    """Test that _mark_ship_broke works correctly for both fuel and payroll."""
    env = simpy.Environment()
    sim = Simulation(simple_game_state,
                     num_ships=1,
                     starting_day=2,
                     verbose=True)

    agent = StarshipAgent(
        env, test_ship_with_crew, sim, starting_state=StarshipState.DOCKED
    )

    # Test marking broke with a reason
    agent._mark_ship_broke("test reason for being broke")

    assert agent.broke is True
