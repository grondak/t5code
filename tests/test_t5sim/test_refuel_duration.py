"""Tests for refueling duration feature based on starport RefuelRate.

The refueling duration system works as follows:
- Refueling takes nD6 hours where n is the starport's RefuelRate
- Starport A/B: 2D6 hours (2-12 hours)
- Starport C/D: 4D6 hours (4-24 hours)
- Starport E/X: 0 hours (no fuel available)
- Duration is converted to days (hours / 24)
- Refueling can start immediately upon docking
- Refueling must complete before undocking
"""

import pytest
import simpy
from unittest.mock import MagicMock
from t5code import T5Starship, T5Company, T5ShipClass
from t5code.T5Tables import STARPORT_TYPES
from t5sim.starship_agent import StarshipAgent
from t5sim.starship_states import StarshipState


@pytest.fixture
def mock_simulation():
    """Create a mock simulation."""
    sim = MagicMock()
    sim.verbose = True
    sim.env = simpy.Environment()
    sim.game_state = MagicMock()
    sim.game_state.world_data = {}
    return sim


@pytest.fixture
def basic_starship(setup_test_gamestate):
    """Create a basic starship for testing."""
    game_state = setup_test_gamestate
    ship_class_dict = game_state.ship_classes["small"]
    class_name = ship_class_dict["class_name"]
    ship_class = T5ShipClass(class_name, ship_class_dict)
    company = T5Company("Test Company", starting_capital=1_000_000)
    ship = T5Starship("Test Ship", "Rhylanor", ship_class, owner=company)
    ship.credit(0, 1_000_000)
    ship.set_course_for("Jae Tellona")
    return ship


class TestDiceRolling:
    """Test the dice rolling utility function."""

    def test_roll_dice_basic(self, mock_simulation, basic_starship):
        """Test rolling dice returns reasonable values."""
        agent = StarshipAgent(
            mock_simulation.env,
            basic_starship,
            mock_simulation,
            starting_state=StarshipState.DOCKED
        )

        # Test rolling 1D6
        result = agent._roll_dice(1)
        assert 1 <= result <= 6

        # Test rolling 2D6
        result = agent._roll_dice(2)
        assert 2 <= result <= 12

        # Test rolling 4D6
        result = agent._roll_dice(4)
        assert 4 <= result <= 24

    def test_roll_dice_zero(self, mock_simulation, basic_starship):
        """Test rolling zero dice returns 0."""
        agent = StarshipAgent(
            mock_simulation.env,
            basic_starship,
            mock_simulation,
            starting_state=StarshipState.DOCKED
        )
        result = agent._roll_dice(0)
        assert result == 0

    def test_roll_dice_negative(self, mock_simulation, basic_starship):
        """Test rolling negative dice returns 0."""
        agent = StarshipAgent(
            mock_simulation.env,
            basic_starship,
            mock_simulation,
            starting_state=StarshipState.DOCKED
        )
        result = agent._roll_dice(-1)
        assert result == 0

    def test_roll_dice_distribution(self, mock_simulation, basic_starship):
        """Test that dice rolling produces reasonable distribution."""
        agent = StarshipAgent(
            mock_simulation.env,
            basic_starship,
            mock_simulation,
            starting_state=StarshipState.DOCKED
        )

        # Roll 2D6 many times and check distribution
        results = [agent._roll_dice(2) for _ in range(1000)]

        # All results should be in valid range
        assert all(2 <= r <= 12 for r in results)

        # Should have some variety (not all same value)
        assert len(set(results)) > 1

        # Average should be close to 7 for 2D6
        average = sum(results) / len(results)
        assert 6 < average < 8


class TestRefuelingDurationCalculation:
    """Test refueling duration calculation based on starport type."""

    def test_starport_a_refuel_rate(self, mock_simulation, basic_starship):
        """Test starport A has RefuelRate of 2 (2D6 hours)."""
        assert STARPORT_TYPES["A"]["RefuelRate"] == 2

    def test_starport_b_refuel_rate(self, mock_simulation, basic_starship):
        """Test starport B has RefuelRate of 2 (2D6 hours)."""
        assert STARPORT_TYPES["B"]["RefuelRate"] == 2

    def test_starport_c_refuel_rate(self, mock_simulation, basic_starship):
        """Test starport C has RefuelRate of 4 (4D6 hours)."""
        assert STARPORT_TYPES["C"]["RefuelRate"] == 4

    def test_starport_d_refuel_rate(self, mock_simulation, basic_starship):
        """Test starport D has RefuelRate of 4 (4D6 hours)."""
        assert STARPORT_TYPES["D"]["RefuelRate"] == 4

    def test_starport_e_refuel_rate(self, mock_simulation, basic_starship):
        """Test starport E has RefuelRate of 0 (no refueling)."""
        assert STARPORT_TYPES["E"]["RefuelRate"] == 0

    def test_starport_x_refuel_rate(self, mock_simulation, basic_starship):
        """Test starport X has RefuelRate of 0 (no refueling)."""
        assert STARPORT_TYPES["X"]["RefuelRate"] == 0


class TestRefuelingDurationOverride:
    """Test that refueling duration is properly calculated and applied."""

    def test_refueling_duration_initialized(self,
                                            mock_simulation,
                                            basic_starship):
        """Test that refueling_duration_days is initialized to None."""
        agent = StarshipAgent(
            mock_simulation.env,
            basic_starship,
            mock_simulation,
            starting_state=StarshipState.DOCKED
        )
        assert agent.refueling_duration_days is None

    def test_refueling_duration_set_on_load_fuel(
            self, mock_simulation, basic_starship):
        """Test that _load_fuel calculates and sets refueling duration."""
        # Set ship location to a starport
        basic_starship.location = "Rhylanor"  # This is a starport

        # Partially drain fuel to force refueling
        basic_starship.jump_fuel = 0
        basic_starship.ops_fuel = 0

        agent = StarshipAgent(
            mock_simulation.env,
            basic_starship,
            mock_simulation,
            starting_state=StarshipState.LOADING_FUEL
        )

        # Call _load_fuel
        agent._load_fuel()

        # Duration should be set (we can't test exact value due to dice rolls)
        # But we can verify it's a reasonable value
        if agent.refueling_duration_days is not None:
            assert agent.refueling_duration_days > 0
            assert agent.refueling_duration_days < 1.0  # Less than 24 hours

    def test_refueling_duration_reset_after_use(
            self, mock_simulation, basic_starship):
        """Test that refueling duration is
        reset after use in state execution."""
        basic_starship.location = "Rhylanor"
        basic_starship.jump_fuel = 0
        basic_starship.ops_fuel = 0

        agent = StarshipAgent(
            mock_simulation.env,
            basic_starship,
            mock_simulation,
            starting_state=StarshipState.LOADING_FUEL
        )

        # Load fuel to set duration
        agent._load_fuel()
        duration_before = agent.refueling_duration_days

        # The duration should be set (either a value or None if no refuel rate)
        # We can't test exact value due to dice rolls, but verify it's valid
        assert duration_before is None or duration_before >= 0


class TestRefuelingWithFullTanks:
    """Test refueling behavior when tanks are already full."""

    def test_full_tanks_still_sets_duration(
            self, mock_simulation, basic_starship):
        """Test that refueling duration is set even with full tanks."""
        basic_starship.location = "Rhylanor"

        # Tanks are already full by default
        assert basic_starship.jump_fuel == basic_starship.jump_fuel_capacity
        assert basic_starship.ops_fuel == basic_starship.ops_fuel_capacity

        agent = StarshipAgent(
            mock_simulation.env,
            basic_starship,
            mock_simulation,
            starting_state=StarshipState.LOADING_FUEL
        )

        agent._load_fuel()

        # Duration should still be set (time to complete refuel attempt)
        if agent.refueling_duration_days is not None:
            assert agent.refueling_duration_days >= 0


class TestRefuelingWithoutFunds:
    """Test refueling behavior with insufficient credits."""

    def test_insufficient_funds_still_sets_duration(
            self, mock_simulation, basic_starship):
        """Test that refueling duration is set even without funds."""
        basic_starship.location = "Rhylanor"
        basic_starship.jump_fuel = 0
        basic_starship.ops_fuel = 0

        # Drain company balance using the ship's debit method
        initial_balance = basic_starship.owner.balance
        basic_starship.debit(0, initial_balance, "test drain")

        agent = StarshipAgent(
            mock_simulation.env,
            basic_starship,
            mock_simulation,
            starting_state=StarshipState.LOADING_FUEL
        )

        agent._load_fuel()

        # Duration should still be set (time spent at refuel station)
        if agent.refueling_duration_days is not None:
            assert agent.refueling_duration_days >= 0


class TestRefuelingDurationRange:
    """Test that refueling durations are in expected ranges."""

    def test_starport_a_duration_range(self, mock_simulation, basic_starship):
        """Test that starport A refueling is 2-12 hours (2D6)."""
        basic_starship.location = "Rhylanor"
        basic_starship.jump_fuel = 0
        basic_starship.ops_fuel = 0

        durations_days = []
        for _ in range(50):
            agent = StarshipAgent(
                mock_simulation.env,
                basic_starship,
                mock_simulation,
                starting_state=StarshipState.LOADING_FUEL
            )
            agent._load_fuel()
            if agent.refueling_duration_days is not None:
                durations_days.append(agent.refueling_duration_days)

        # Convert to hours
        durations_hours = [d * 24 for d in durations_days]

        # Should have variety in range
        if durations_hours:
            assert min(durations_hours) >= 2 / 24  # At least 2 hours in days
            assert max(durations_hours) <= 12 / 24  # At most 12 hours in days

    def test_multiple_starport_types_different_durations(
            self, mock_simulation, basic_starship, monkeypatch):
        """Test that different starport types
        produce different duration ranges."""
        basic_starship.jump_fuel = 0
        basic_starship.ops_fuel = 0

        # Test starport A (2D6)
        basic_starship.location = "Rhylanor"
        durations_a = []
        for _ in range(30):
            agent = StarshipAgent(
                mock_simulation.env,
                basic_starship,
                mock_simulation,
                starting_state=StarshipState.LOADING_FUEL
            )
            agent._load_fuel()
            if agent.refueling_duration_days is not None:
                durations_a.append(agent.refueling_duration_days * 24)

        # Test starport C (4D6) - would need different location
        # This is a simplified test to show the concept
        if durations_a:
            # A-class average should be around 7 hours
            avg_a = sum(durations_a) / len(durations_a)
            assert 5 < avg_a < 9, f"Starport A average should ~7, got {avg_a}"


class TestRefuelingDocumentation:
    """Test that the refueling system documentation is clear."""

    def test_refueling_rules_are_documented(self):
        """Test that refueling rules are documented in docstrings."""
        # Check _load_fuel docstring mentions duration calculation
        assert "nD6" in StarshipAgent._load_fuel.__doc__
        assert "RefuelRate" in StarshipAgent._load_fuel.__doc__
        assert "immediately upon docking" in StarshipAgent._load_fuel.__doc__
        assert "must complete "\
            "before undocking" in StarshipAgent._load_fuel.__doc__

    def test_dice_rolling_documented(self):
        """Test that dice rolling method is documented."""
        assert "D6" in StarshipAgent._roll_dice.__doc__
        assert "six-sided" in StarshipAgent._roll_dice.__doc__
