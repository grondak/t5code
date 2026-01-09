"""Tests for uncovered branches in starship_agent and T5Starship."""

import pytest
import simpy
from unittest.mock import MagicMock
from t5code import T5Starship, T5Company, T5ShipClass
from t5code.GameState import GameState, load_and_parse_t5_map
from t5code.T5World import T5World
from t5sim.starship_agent import StarshipAgent
from t5sim.starship_states import StarshipState


@pytest.fixture
def setup_test_gamestate():
    """Setup GameState instance for tests."""
    MAP_FILE = "tests/test_t5code/t5_test_map.txt"
    game_state = GameState()
    game_state.world_data = T5World.load_all_worlds(
        load_and_parse_t5_map(MAP_FILE))
    from t5code.GameState import load_and_parse_t5_ship_classes
    game_state.ship_classes = load_and_parse_t5_ship_classes(
        "resources/t5_ship_classes.csv")
    return game_state


class TestStarshipAgentCoverageGaps:
    """Test uncovered branches in starship_agent.py."""

    def test_starting_year_type_error_exception(self, setup_test_gamestate):
        """Test exception handling when starting_year causes TypeError."""
        env = simpy.Environment()
        sim = MagicMock()
        sim.env = env
        sim.verbose = False
        sim.game_state = setup_test_gamestate

        # Create a starship
        ship_class_dict = setup_test_gamestate.ship_classes["Free Trader"]
        ship_class = T5ShipClass("Free Trader", ship_class_dict)
        company = T5Company("Test Co", starting_capital=1000000)
        ship = T5Starship("TestShip", "Rhylanor", ship_class, owner=company)
        ship.credit(0, 500000)

        agent = StarshipAgent(env,
                              ship,
                              sim,
                              starting_state=StarshipState.MAINTENANCE)

        # Set starting_year to something that will cause TypeError
        sim.starting_year = MagicMock()
        sim.starting_year.__int__ = MagicMock(
            side_effect=TypeError("mock error"))
        sim.starting_day = MagicMock()
        sim.starting_day.__int__ = MagicMock(
            side_effect=TypeError("mock error"))

        # Should handle the exception and use default values
        # This should not raise an exception
        try:
            agent._perform_maintenance()
        except TypeError:
            pytest.fail("Should have caught TypeError exception")

    def test_maintenance_with_zero_profit_no_report(self,
                                                    setup_test_gamestate):
        """Test maintenance when annual profit is zero or negative."""
        env = simpy.Environment()
        sim = MagicMock()
        sim.env = env
        sim.verbose = False
        sim.game_state = setup_test_gamestate

        # Create a starship
        ship_class_dict = setup_test_gamestate.ship_classes["Free Trader"]
        ship_class = T5ShipClass("Free Trader", ship_class_dict)
        company = T5Company("Test Co", starting_capital=500000)
        ship = T5Starship("TestShip", "Rhylanor", ship_class, owner=company)

        agent = StarshipAgent(env,
                              ship,
                              sim,
                              starting_state=StarshipState.MAINTENANCE)

        # Set last_year_balance equal to current balance
        # This means zero profit, so we skip the profit reporting code
        agent.last_year_balance = 500000

        # Should complete without reporting profit
        agent._perform_maintenance()

        # Should not be broke and maintenance should be done
        assert ship.needs_maintenance is False

    def test_maintenance_with_crew_profit_share_payment(self,
                                                        setup_test_gamestate):
        """Test maintenance when ship can pay crew profit share."""
        env = simpy.Environment()
        sim = MagicMock()
        sim.env = env
        sim.verbose = False
        sim.game_state = setup_test_gamestate

        # Create a starship
        ship_class_dict = setup_test_gamestate.ship_classes["Free Trader"]
        ship_class = T5ShipClass("Free Trader", ship_class_dict)
        company = T5Company("Test Co", starting_capital=1000000)
        ship = T5Starship("TestShip", "Rhylanor", ship_class, owner=company)
        ship.credit(0, 1000000)

        agent = StarshipAgent(env,
                              ship,
                              sim,
                              starting_state=StarshipState.MAINTENANCE)

        # Set up profit scenario
        agent.last_year_balance = 500000  # So profit is 500k

        # Now have plenty of funds for crew profit share
        # Crew share = 50k (10% of 500k)
        # Plus maintenance costs

        agent._perform_maintenance()

        # Should not be broke
        assert agent.broke is False
        assert ship.needs_maintenance is False
        # last_year_balance should be updated
        assert agent.last_year_balance == ship.owner.balance

    def test_maintenance_with_insufficient_funds_for_crew_share(
            self,
            setup_test_gamestate):
        """Test maintenance when ship can't afford
        crew profit share (lines 560-564)."""
        env = simpy.Environment()
        sim = MagicMock()
        sim.env = env
        sim.verbose = False
        sim.game_state = setup_test_gamestate

        # Create a starship
        ship_class_dict = setup_test_gamestate.ship_classes["Free Trader"]
        ship_class = T5ShipClass("Free Trader", ship_class_dict)
        company = T5Company("Test Co", starting_capital=100)
        ship = T5Starship("TestShip", "Rhylanor", ship_class, owner=company)
        # Don't add extra credit - just use the starting balance of 100

        agent = StarshipAgent(env,
                              ship,
                              sim,
                              starting_state=StarshipState.MAINTENANCE)

        # To hit the crew share insufficient funds condition at lines 560-564:
        # We need: annual_profit > 0 AND self.ship.owner.balance < crew_share
        # Where crew_share = int(annual_profit * 0.10)
        #
        # current_balance = 100
        # annual_profit = current_balance - last_year_balance
        # If last_year_balance = -10000:
        #   annual_profit = 100 - (-10000) = 10100
        #   crew_share = int(10100 * 0.10) = 1010
        #   balance (100) < crew_share (1010) ✓

        agent.last_year_balance = -10000

        # Should mark ship as broke due to insufficient crew profit share funds
        agent._perform_maintenance()

        # Should be broke
        assert agent.broke is True

    def test_maintenance_with_insufficient_funds_for_maintenance(
            self,
            setup_test_gamestate):
        """Test maintenance when ship can't afford maintenance costs."""
        env = simpy.Environment()
        sim = MagicMock()
        sim.env = env
        sim.verbose = False
        sim.game_state = setup_test_gamestate

        # Create a starship
        ship_class_dict = setup_test_gamestate.ship_classes["Free Trader"]
        ship_class = T5ShipClass("Free Trader", ship_class_dict)
        company = T5Company("Test Co", starting_capital=10000)
        ship = T5Starship("TestShip", "Rhylanor", ship_class, owner=company)

        agent = StarshipAgent(env,
                              ship,
                              sim,
                              starting_state=StarshipState.MAINTENANCE)

        # Set last_year_balance to trigger profit calculation
        # Profit is 5k, too small for crew share check
        agent.last_year_balance = 5000

        # Ship has only 10k, Free Trader
        # maintenance ~61k (1/1000 of 61.1 MCr ship_cost)
        agent._perform_maintenance()

        # Should be broke due to insufficient maintenance funds
        assert agent.broke is True


class TestT5StarshipCoverageGaps:
    """Test uncovered branches in T5Starship.py."""

    def test_profitable_cargo_at_world_without_refined_fuel(
            self, setup_test_gamestate):
        """Test that ships skip profitable cargo
        if destination lacks refined fuel.

        This tests the uncovered line 1054 which continues when a destination
        doesn't have refined fuel for ships that can't refine fuel themselves.
        """
        ship_class_dict = setup_test_gamestate.ship_classes["Free Trader"]
        ship_class = T5ShipClass("Free Trader", ship_class_dict)
        company = T5Company("Test Co", starting_capital=1000000)
        ship = T5Starship("TestShip", "Rhylanor", ship_class, owner=company)
        ship.credit(0, 500000)

        # Ensure this ship can't refine fuel
        ship.can_refine_fuel = False

        # Try to find profitable cargo destinations
        # The method should skip worlds without refined fuel
        destinations = ship.find_profitable_destinations(setup_test_gamestate)

        # Verify that any destinations returned have refined fuel
        # (or that the filter worked properly)
        if destinations:
            for world_name, profit in destinations:
                world = setup_test_gamestate.world_data.get(world_name)
                if world:
                    sp_type = world.get_starport()
                    from t5code.T5Tables import STARPORT_TYPES
                    sp_info = STARPORT_TYPES.get(sp_type, {})
                    # For ships that can't refine,
                    # refined fuel must be available
                    # (this is what line 1054 enforces)
                    assert sp_info.get("RefinedFuel", False), \
                        f"World {world_name} lacks "
                    "refined fuel but was returned"
