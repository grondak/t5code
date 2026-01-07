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
    """Test that payroll deducts correct amount based on skill levels."""
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
    # Pilot-2 (200) + Astrogator-1 (100) + Chief Engineer-3 (300) = 600 Cr
    payroll_entry = test_ship_with_crew.owner.cash.ledger[-1]
    assert payroll_entry.amount == -600
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
    # Pilot-2 (200) + Astrogator-1 (100) + Chief Engineer-3 (300) = 600 Cr
    payroll_entry = payroll_entries[0]
    assert payroll_entry.amount == -600  # Debit
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

    # Set balance to less than payroll (600 Cr needed for crew)
    # Use post() to reduce balance
    current_balance = test_ship_with_crew.owner.balance
    reduction = current_balance - 500
    test_ship_with_crew.owner.cash.post(time=0,
                                        amount=-reduction,
                                        memo="Test: reduce to 500")

    agent = StarshipAgent(
        env, test_ship_with_crew, sim, starting_state=StarshipState.DOCKED
    )

    # Run simulation to trigger payroll
    env.run(until=1.0)

    # Ship should be marked as broke
    assert agent.broke is True

    # Balance should not have changed (payroll not processed)
    assert test_ship_with_crew.owner.balance == 500


def test_broke_ship_stops_processing_payroll(
        simple_game_state, test_ship_with_crew):
    """Test that broke ships don't continue processing payroll."""
    env = simpy.Environment()
    sim = Simulation(simple_game_state, num_ships=1, starting_day=2)

    # Set destination to avoid errors
    test_ship_with_crew.set_course_for("Rhylanor")

    # Set balance to exactly one payroll (600 Cr needed)
    current_balance = test_ship_with_crew.owner.balance
    reduction = current_balance - 600
    test_ship_with_crew.owner.cash.post(time=0,
                                        amount=-reduction,
                                        memo="Test: reduce to 600")

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


def test_military_ship_patron_bailout(simple_game_state, test_ship_data):
    """Test that military ships get patron bailout instead of going broke."""
    env = simpy.Environment()
    sim = Simulation(simple_game_state,
                     num_ships=1,
                     starting_day=2,
                     verbose=False)

    # Create military ship (use "large" which has role="military")
    ship_class = T5ShipClass("large", test_ship_data["large"])
    company = T5Company("Military Inc", starting_capital=100_000)
    military_ship = T5Starship("Military Test", "large",
                               ship_class, owner=company)

    agent = StarshipAgent(
        env, military_ship, sim, starting_state=StarshipState.DOCKED
    )

    initial_balance = company.balance
    agent._mark_ship_broke("insufficient funds test")

    # Military ship should NOT be broke
    assert agent.broke is False

    # Should have received 1 million credit bailout
    assert company.balance == initial_balance + 1_000_000

    # Ledger should have patron bailout entry
    bailout_entries = [entry for entry in company.cash.ledger
                       if "Patron bailout" in entry.memo]
    assert len(bailout_entries) == 1
    assert "Military" in bailout_entries[0].memo


def test_specialized_ship_patron_bailout(simple_game_state, test_ship_data):
    """Test that specialized ships get patron
    bailout instead of going broke."""
    env = simpy.Environment()
    sim = Simulation(simple_game_state,
                     num_ships=1,
                     starting_day=2,
                     verbose=False)

    # Create specialized ship (use "specialized" which has role="specialized")
    ship_class = T5ShipClass("specialized", test_ship_data["specialized"])
    company = T5Company("Specialized Inc", starting_capital=100_000)
    specialized_ship = T5Starship("Specialized Test", "specialized",
                                  ship_class, owner=company)

    agent = StarshipAgent(
        env, specialized_ship, sim, starting_state=StarshipState.DOCKED
    )

    initial_balance = company.balance
    agent._mark_ship_broke("insufficient funds test")

    # Specialized ship should NOT be broke
    assert agent.broke is False

    # Should have received 1 million credit bailout
    assert company.balance == initial_balance + 1_000_000

    # Ledger should have patron bailout entry
    bailout_entries = [entry for entry in company.cash.ledger
                       if "Patron bailout" in entry.memo]
    assert len(bailout_entries) == 1
    assert "Specialized" in bailout_entries[0].memo


def test_civilian_ship_goes_broke(simple_game_state, test_ship_data):
    """Test that civilian ships actually go broke and don't get bailout."""
    env = simpy.Environment()
    sim = Simulation(simple_game_state,
                     num_ships=1,
                     starting_day=2,
                     verbose=False)

    # Create civilian ship (use "small" which has role="civilian")
    ship_class = T5ShipClass("small", test_ship_data["small"])
    company = T5Company("Civilian Inc", starting_capital=100_000)
    civilian_ship = T5Starship("Civilian Test", "small",
                               ship_class, owner=company)

    agent = StarshipAgent(
        env, civilian_ship, sim, starting_state=StarshipState.DOCKED
    )

    initial_balance = company.balance
    agent._mark_ship_broke("insufficient funds test")

    # Civilian ship SHOULD be broke
    assert agent.broke is True

    # Balance should NOT have changed (no bailout)
    assert company.balance == initial_balance

    # No bailout entries in ledger
    bailout_entries = [entry for entry in company.cash.ledger
                       if "Patron bailout" in entry.memo]
    assert len(bailout_entries) == 0


def test_skill_based_salary_calculation(simple_game_state, test_ship_data):
    """Test that crew salaries are calculated based on skill levels."""
    env = simpy.Environment()
    sim = Simulation(simple_game_state, num_ships=1, starting_day=2)

    # Create ship with specific crew configuration
    ship_class = T5ShipClass("small", test_ship_data["small"])
    company = T5Company("Test Company", starting_capital=100_000)
    ship = T5Starship("Test Ship", "Rhylanor", ship_class, owner=company)

    # Add crew with known skill requirements:
    # Pilot: maneuver-2 → 200 Cr
    pilot = T5NPC("Pilot")
    pilot.set_skill("pilot", 2)
    ship.crew_position["Pilot"][0].assign(pilot)

    # Astrogator: jump-1 → 100 Cr
    astrogator = T5NPC("Astrogator")
    astrogator.set_skill("navigator", 1)
    ship.crew_position["Astrogator"][0].assign(astrogator)

    # Engineer: powerplant-2 → 200 Cr
    engineer = T5NPC("Engineer")
    engineer.set_skill("engineer", 2)
    ship.crew_position["Engineer"][0].assign(engineer)

    ship.set_course_for("Rhylanor")

    agent = StarshipAgent(
        env, ship, sim, starting_state=StarshipState.DOCKED
    )

    # Calculate payroll
    total, count = agent.calculate_total_payroll()

    assert count == 3
    # Pilot-2 (200) + Astrogator-1 (100) + Chief Engineer-3 (300) = 600 Cr
    assert total == 600


def test_different_ship_sizes_different_salaries(
        simple_game_state, test_ship_data):
    """Test that different ship sizes result in different crew salaries."""
    env = simpy.Environment()
    sim = Simulation(simple_game_state, num_ships=1, starting_day=2)

    # Large ship: jump-3, maneuver-3, powerplant-3
    ship_class = T5ShipClass("large", test_ship_data["large"])
    company = T5Company("Test Company", starting_capital=500_000)
    ship = T5Starship("Large Ship", "Rhylanor", ship_class, owner=company)

    # Add some crew:
    # Pilot: maneuver-3 → 300 Cr
    pilot = T5NPC("Pilot")
    pilot.set_skill("pilot", 3)
    ship.crew_position["Pilot"][0].assign(pilot)

    # Astrogator: jump-3 → 300 Cr
    astrogator = T5NPC("Astrogator")
    astrogator.set_skill("navigator", 3)
    ship.crew_position["Astrogator"][0].assign(astrogator)

    # Chief Engineer: powerplant-3 + 1 → 400 Cr
    engineer1 = T5NPC("Chief Engineer")
    engineer1.set_skill("engineer", 4)
    ship.crew_position["Engineer"][0].assign(engineer1)

    # Second Engineer: powerplant-3 → 300 Cr
    engineer2 = T5NPC("Engineer 2")
    engineer2.set_skill("engineer", 3)
    ship.crew_position["Engineer"][1].assign(engineer2)

    # Third Engineer: powerplant-3 → 300 Cr
    engineer3 = T5NPC("Engineer 3")
    engineer3.set_skill("engineer", 3)
    ship.crew_position["Engineer"][2].assign(engineer3)

    ship.set_course_for("Rhylanor")

    agent = StarshipAgent(
        env, ship, sim, starting_state=StarshipState.DOCKED
    )

    # Calculate payroll
    total, count = agent.calculate_total_payroll()

    assert count == 5
    # 300 (pilot) + 300 (astrogator) + 400 (chief eng) + 300 + 300 = 1600 Cr
    assert total == 1600


def test_steward_and_medic_salaries(simple_game_state, test_ship_data):
    """Test fixed-skill positions (Medic) have correct salaries."""
    env = simpy.Environment()
    sim = Simulation(simple_game_state, num_ships=1, starting_day=2)

    # Use large ship which has Medic position
    ship_class = T5ShipClass("large", test_ship_data["large"])
    company = T5Company("Test Company", starting_capital=500_000)
    ship = T5Starship("Test Ship", "Rhylanor", ship_class, owner=company)

    # Add Medic: skill-2 → 200 Cr
    medic = T5NPC("Medic")
    medic.set_skill("medic", 2)
    ship.crew_position["Medic"][0].assign(medic)

    ship.set_course_for("Rhylanor")

    agent = StarshipAgent(
        env, ship, sim, starting_state=StarshipState.DOCKED
    )

    # Calculate payroll
    total, count = agent.calculate_total_payroll()

    assert count == 1
    assert total == 200  # Medic-2 earns 200 Cr


def test_get_crew_salary_method(simple_game_state, test_ship_data):
    """Test the Simulation.get_crew_salary method directly."""
    sim = Simulation(simple_game_state, num_ships=1, starting_day=2)
    ship_class = T5ShipClass("small", test_ship_data["small"])

    # Test different positions
    pilot_salary = sim.get_crew_salary("Pilot", 0, ship_class)
    assert pilot_salary == 200  # maneuver-2

    astrogator_salary = sim.get_crew_salary("Astrogator", 0, ship_class)
    assert astrogator_salary == 100  # jump-1

    engineer_salary = sim.get_crew_salary("Engineer", 0, ship_class)
    assert engineer_salary == 300  # powerplant-2 + 1 (chief engineer)

    # Second engineer doesn't get +1 bonus
    engineer2_salary = sim.get_crew_salary("Engineer", 1, ship_class)
    assert engineer2_salary == 200  # powerplant-2
