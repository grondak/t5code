"""Test the main simulation orchestrator."""

import pytest
from unittest.mock import patch
from t5code import GameState as gs_module, T5World, T5ShipClass
from t5code.GameState import GameState
from t5sim import Simulation
from t5code.T5NPC import generate_captain_risk_profile


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
    # All ships should have crew and owner companies with starting capital
    for agent in sim.agents:
        assert agent.ship.owner is not None
        assert agent.ship.owner.balance == sim.starting_capital
        # Check crew_position has filled positions
        total_crew = sum(
            sum(1 for pos in positions if pos.is_filled())
            for positions in agent.ship.crew_position.values()
        )
        assert total_crew > 0


def test_simulation_run_short(game_state):
    """Test running simulation for short duration."""
    sim = Simulation(game_state, num_ships=2, duration_days=1.0)
    results = sim.run()

    assert results["num_ships"] == 2
    assert results["duration_days"] == pytest.approx(1.0)
    assert "total_voyages" in results
    assert "ships" in results
    assert len(results["ships"]) == 2


def test_simulation_record_cargo_sale(game_state):
    """Test recording cargo sales."""
    sim = Simulation(game_state, num_ships=1, duration_days=1.0)

    # Record a cargo sale
    sim.record_cargo_sale("TestShip", "Regina", 5000.0)

    # Check it was recorded
    assert len(sim.statistics["cargo_sales"]) == 1
    sale = sim.statistics["cargo_sales"][0]
    assert sale["ship"] == "TestShip"
    assert sale["location"] == "Regina"
    assert sale["profit"] == pytest.approx(5000.0)
    assert "time" in sale


def test_format_traveller_date_default_start(game_state):
    """Test Traveller date formatting with default starting date."""
    sim = Simulation(game_state, num_ships=1, duration_days=10.0)

    # Default is 360-1104, now with fractional days
    assert sim.format_traveller_date(0.0) == "360.00-1104"
    assert sim.format_traveller_date(1.0) == "361.00-1104"
    assert sim.format_traveller_date(1.5) == "361.50-1104"
    assert sim.format_traveller_date(5.0) == "365.00-1104"
    assert sim.format_traveller_date(6.0) == "001.00-1105"  # Year rollover
    assert sim.format_traveller_date(10.0) == "005.00-1105"


def test_format_traveller_date_custom_start(game_state):
    """Test Traveller date formatting with custom starting date."""
    sim = Simulation(game_state, num_ships=1, duration_days=10.0,
                     starting_year=1105, starting_day=1)

    assert sim.format_traveller_date(0.0) == "001.00-1105"
    assert sim.format_traveller_date(1.0) == "002.00-1105"
    assert sim.format_traveller_date(1.25) == "002.25-1105"
    assert sim.format_traveller_date(364.0) == "365.00-1105"
    assert sim.format_traveller_date(365.0) == "001.00-1106"  # Year rollover


def test_format_traveller_date_mid_year(game_state):
    """Test Traveller date formatting starting mid-year."""
    sim = Simulation(game_state, num_ships=1, duration_days=10.0,
                     starting_year=1104, starting_day=180)

    assert sim.format_traveller_date(0.0) == "180.00-1104"
    assert sim.format_traveller_date(0.75) == "180.75-1104"
    assert sim.format_traveller_date(185.0) == "365.00-1104"
    assert sim.format_traveller_date(186.0) == "001.00-1105"  # Year rollover


def test_run_simulation_function():
    """Test the run_simulation convenience function
    loads data and runs simulation."""
    from t5sim.simulation import run_simulation

    # Call the actual function with test data
    results = run_simulation(
        map_file="tests/test_t5code/t5_test_map.txt",
        ship_classes_file="resources/t5_ship_classes.csv",
        num_ships=2,
        duration_days=1.0
    )

    # Verify it returns expected structure
    assert results["num_ships"] == 2
    assert results["duration_days"] == pytest.approx(1.0)
    assert "total_profit" in results
    assert "cargo_sales" in results
    assert "ships" in results
    assert len(results["ships"]) == 2
    assert "total_voyages" in results


def test_generate_captain_risk_profile_very_cautious():
    """Test very cautious captain risk profile (91-95%)."""
    # Force roll between 0.90 and 0.98 for very cautious
    with patch('t5code.T5NPC.random.random', return_value=0.95):
        with patch('t5code.T5NPC.random.uniform', return_value=0.93):
            threshold = generate_captain_risk_profile()
            assert threshold == pytest.approx(0.93)


def test_generate_captain_risk_profile_aggressive():
    """Test aggressive captain risk profile (65-69%)."""
    # Force roll above 0.98 for aggressive
    with patch('t5code.T5NPC.random.random', return_value=0.99):
        with patch('t5code.T5NPC.random.uniform', return_value=0.67):
            threshold = generate_captain_risk_profile()
            assert threshold == pytest.approx(0.67)


def test_get_skill_for_position_gunner(game_state):
    """Test _get_skill_for_position returns correct skill for Gunner."""
    sim = Simulation(game_state, num_ships=1, duration_days=1.0)

    # Create a ship class with gunner position
    ship_data = {
        "class_name": "test_gunship",
        "jump_rating": 2,
        "maneuver_rating": 3,
        "powerplant_rating": 3,
        "cargo_capacity": 50,
        "staterooms": 5,
        "low_berths": 0,
        "crew_positions": ["G"]  # Gunner
    }
    ship_class = T5ShipClass("test_gunship", ship_data)

    skill = sim._get_skill_for_position("Gunner", 0, ship_class)
    assert skill == ("Gunner", 1)


def test_get_skill_for_position_counsellor(game_state):
    """Test _get_skill_for_position returns correct skill for Counsellor."""
    sim = Simulation(game_state, num_ships=1, duration_days=1.0)

    # Create a ship class with counsellor position
    ship_data = {
        "class_name": "test_counsellor_ship",
        "jump_rating": 2,
        "maneuver_rating": 3,
        "powerplant_rating": 3,
        "cargo_capacity": 50,
        "staterooms": 5,
        "low_berths": 0,
        "crew_positions": ["O"]  # Counsellor
    }
    ship_class = T5ShipClass("test_counsellor_ship", ship_data)

    skill = sim._get_skill_for_position("Counsellor", 0, ship_class)
    assert skill == ("Counsellor", 2)


def test_print_ledger(game_state, capsys):
    """Test print_ledger outputs correctly formatted ledger."""
    sim = Simulation(game_state, num_ships=1, duration_days=10.0)
    sim.setup()

    # Get the ship
    ship = sim.agents[0].ship
    ship_name = ship.ship_name
    company = ship.owner

    # Add some transactions via the ship
    ship.credit(0, 50000, "Test credit")
    ship.debit(1, 10000, "Test debit")

    # Print the ledger
    sim.print_ledger(ship_name)

    captured = capsys.readouterr()
    assert f"LEDGER FOR {company.name}" in captured.out
    # Now includes ship class and location
    assert f"({ship_name}," in captured.out
    assert ship.ship_class in captured.out
    assert "@" in captured.out  # Location separator
    assert f"Final Balance: Cr{company.balance:,.0f}" in captured.out
    assert "Test credit" in captured.out
    assert "Test debit" in captured.out


def test_print_ledger_invalid_ship(game_state):
    """Test print_ledger raises ValueError for invalid ship name."""
    sim = Simulation(game_state, num_ships=1, duration_days=10.0)
    sim.setup()

    with pytest.raises(ValueError, match="Ship 'InvalidShip' not found"):
        sim.print_ledger("InvalidShip")


def test_print_all_ledgers(game_state, capsys):
    """Test print_all_ledgers outputs ledgers for all ships."""
    sim = Simulation(game_state, num_ships=2, duration_days=10.0)
    sim.setup()

    # Add transactions to both ships
    for agent in sim.agents:
        agent.ship.credit(0, 25000, "Initial credit")

    sim.print_all_ledgers()

    captured = capsys.readouterr()
    assert "COMPLETE LEDGER DUMP - ALL SHIPS" in captured.out

    # Check that both ships appear
    for agent in sim.agents:
        assert agent.ship.ship_name in captured.out
        assert agent.ship.owner.name in captured.out
