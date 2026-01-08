"""Tests to improve coverage on starship_agent.py edge cases."""

import unittest
from unittest.mock import Mock, patch
from t5code import GameState as gs_module, T5World
from t5code.GameState import GameState
from t5code import (
    InsufficientFundsError,
    CapacityExceededError
)
from t5sim.simulation import Simulation
from t5sim.starship_agent import StarshipAgent


class TestStarshipAgentCoverage(unittest.TestCase):
    """Test edge cases in StarshipAgent for full coverage."""

    @classmethod
    def setUpClass(cls):
        """Create a shared game state for all tests."""
        cls.game_state = GameState()
        raw_worlds = gs_module.load_and_parse_t5_map(
            "resources/t5_map.txt"
        )
        raw_ships = gs_module.load_and_parse_t5_ship_classes(
            "resources/t5_ship_classes.csv"
        )
        cls.game_state.world_data = T5World.load_all_worlds(raw_worlds)
        cls.game_state.ship_classes = raw_ships

    def test_format_cargo_loading_message_all_zeros(self):
        """Test _format_cargo_loading_message with zero counts.

        Should return empty string when both loaded and skipped
        counts are zero.
        """
        # Setup simulation with minimal config
        sim = Simulation(
            self.game_state,
            num_ships=1,
            duration_days=1.0,
            verbose=False
        )
        sim.setup()

        # Create a ship agent
        agent = sim.agents[0]

        # Call with both counts at zero
        result = agent._format_cargo_loading_message(
            loaded_count=0,
            loaded_mass=0,
            skipped_count=0
        )

        # Should return empty string (line 563)
        self.assertEqual(result, "")

    def test_load_cargo_exception_handling(self):
        """Test _load_cargo handles exceptions during cargo purchase.

        Verifies that the exception handlers catch InsufficientFundsError
        and CapacityExceededError during cargo purchase and break the loop.
        This covers lines 749-750 (exception handlers) and 753-754 (break).
        """
        # Setup simulation with minimal config
        sim = Simulation(
            self.game_state,
            num_ships=1,
            duration_days=1.0,
            verbose=False
        )
        sim.setup()

        agent = sim.agents[0]
        ship = agent.ship

        # Mock world with lots
        mock_world = Mock()
        mock_lot1 = Mock()
        mock_lot2 = Mock()
        mock_world.generate_speculative_cargo.return_value = [
            mock_lot1,
            mock_lot2
        ]

        # Temporarily replace the world in game_state
        original_world = sim.game_state.world_data.get(ship.location)
        sim.game_state.world_data[ship.location] = mock_world

        try:
            # Make ship have space (and ensure hold_size > 0 for Frigates)
            original_cargo_size = ship.cargo_size
            original_hold_size = ship.hold_size
            ship.cargo_size = 0
            if ship.hold_size == 0:
                ship.hold_size = 100

            # First lot succeeds, second raises exception
            call_count = 0

            def side_effect_purchase(*args):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return (True, 10)  # First succeeds
                else:
                    # Alternate between both exception types
                    if call_count % 2 == 0:
                        raise InsufficientFundsError("Not enough funds")
                    else:
                        raise CapacityExceededError("Not enough space")

            with patch.object(
                agent,
                '_try_purchase_lot',
                side_effect=side_effect_purchase
            ):
                # Call _load_cargo - should catch exception and break
                agent._load_cargo()

            # Should have tried to purchase both lots
            self.assertEqual(call_count, 2)
        finally:
            # Restore original world and cargo size
            if original_world:
                sim.game_state.world_data[ship.location] = original_world
            ship.cargo_size = original_cargo_size
            ship.hold_size = original_hold_size

    def test_sell_cargo_exception_handling(self):
        """Test _sell_cargo handles exceptions during sale.

        Verifies that the exception handler catches general exceptions
        during cargo sale and prints an error message without crashing.
        This covers lines 558-564.
        """
        # Setup simulation with minimal config
        sim = Simulation(
            self.game_state,
            num_ships=1,
            duration_days=1.0,
            verbose=False
        )
        sim.setup()

        agent = sim.agents[0]
        ship = agent.ship

        # Create a real cargo lot using the proper constructor
        from t5code import T5Lot

        # Create a cargo lot from the ship's current location
        try:
            lot = T5Lot(ship.location, sim.game_state)
        except Exception:
            self.skipTest("Could not create lot at ship location")

        # Add lot to ship's cargo manifest manually
        if "cargo" not in ship.cargo_manifest:
            ship.cargo_manifest["cargo"] = []
        ship.cargo_manifest["cargo"].append(lot)

        # Mock sell_cargo_lot to raise an exception
        with patch.object(
            ship,
            'sell_cargo_lot',
            side_effect=Exception("Test exception in sale")
        ):
            # Capture print output
            with patch('builtins.print') as mock_print:
                # Call _sell_cargo - should catch exception and print error
                agent._sell_cargo()

                # Verify error was printed
                mock_print.assert_called_once()
                call_args = mock_print.call_args[0][0]
                self.assertIn("Sale error", call_args)
                self.assertIn("Test exception in sale", call_args)

        # Clean up - remove the lot
        ship.cargo_manifest["cargo"] = []

    def test_pilot_as_captain_initialization(self):
        """Test agent initialization when pilot serves
        as captain (line 164)."""
        # Create a ship class with no Captain, only Pilot
        from t5code import T5ShipClass, T5Starship, T5NPC
        ship_class_dict = {
            "class_name": "Scout",
            "jump_rating": 2,
            "maneuver_rating": 2,
            "powerplant_rating": 2,
            "cargo_capacity": 10,
            "staterooms": 0,
            "low_berths": 0,
            # Pilot (A), Astrogator (B), Engineer (E) - no Captain (0)
            "crew_positions": "ABE",
            "crew_ranks": "123"
        }
        ship_class = T5ShipClass("Scout", ship_class_dict)
        from t5code.T5Company import T5Company
        company = T5Company("Test Company", starting_capital=1_000_000)
        ship = T5Starship("Test_Scout", "Rhylanor", ship_class, owner=company)
        ship.credit(0, 1_000_000)

        # Add pilot with cargo threshold
        pilot = T5NPC("Test Pilot")
        pilot.cargo_departure_threshold = 0.75
        ship.crew_position["Pilot"][0].assign(pilot)

        # Create simulation first to get env
        sim = Simulation(self.game_state, num_ships=1, duration_days=1.0)
        # Create agent - should use pilot's threshold (line 164)
        agent = StarshipAgent(sim.env, ship, sim)

        # Verify pilot's threshold is used
        self.assertEqual(agent.minimum_cargo_threshold, 0.75)

    def test_pilot_displayed_as_captain(self):
        """Test pilot is displayed as Captain when
        no explicit captain (line 236)."""
        # Create ship with only Pilot (no Captain)
        from t5code import T5ShipClass, T5Starship, T5NPC
        ship_class_dict = {
            "class_name": "Scout",
            "jump_rating": 2,
            "maneuver_rating": 2,
            "powerplant_rating": 2,
            "cargo_capacity": 10,
            "staterooms": 0,
            "low_berths": 0,
            "crew_positions": "ABE",
            "crew_ranks": "123"
        }
        ship_class = T5ShipClass("Scout", ship_class_dict)
        from t5code.T5Company import T5Company
        company = T5Company("Test Company", starting_capital=1_000_000)
        ship = T5Starship("Test_Scout", "Rhylanor", ship_class, owner=company)

        # Add pilot
        pilot = T5NPC("Test Pilot")
        pilot.set_skill("Pilot", 3)
        pilot.cargo_departure_threshold = 0.75
        ship.crew_position["Pilot"][0].assign(pilot)

        # Create simulation first to get env
        sim = Simulation(self.game_state, num_ships=1, duration_days=1.0)
        # Create agent and get crew info
        agent = StarshipAgent(sim.env, ship, sim)

        crew_info = agent._format_crew_info()
        # Should show "Captain" not "Pilot"
        self.assertIn("Captain", crew_info)
        self.assertIn("75%", crew_info)  # Risk threshold

    def test_frigate_zero_cargo_early_return(self):
        """Test ships with zero cargo capacity return early (line 368)."""
        # Create Frigate with 0 cargo
        from t5code import T5ShipClass, T5Starship
        ship_class_dict = {
            "class_name": "Frigate",
            "jump_rating": 3,
            "maneuver_rating": 3,
            "powerplant_rating": 3,
            "cargo_capacity": 0,
            "staterooms": 0,
            "low_berths": 0,
            "crew_positions": "0BE",
            "crew_ranks": "123"
        }
        ship_class = T5ShipClass("Frigate", ship_class_dict)
        from t5code.T5Company import T5Company
        company = T5Company("Test Company", starting_capital=1_000_000)
        ship = T5Starship("Test_Frigate",
                          "Rhylanor",
                          ship_class,
                          owner=company)

        sim = Simulation(self.game_state, num_ships=1, duration_days=1.0)
        agent = StarshipAgent(sim.env, ship, sim)

        # Should return False immediately without attempting division
        result = agent._should_continue_freight_loading()
        self.assertFalse(result)

    def test_buy_profitable_cargo_lot(self):
        """Test purchasing a profitable cargo lot (lines 666-667)."""
        sim = Simulation(self.game_state, num_ships=1, duration_days=1.0)
        sim.setup()
        agent = sim.agents[0]
        ship = agent.ship

        # Ensure ship has cargo capacity
        if ship.hold_size == 0:
            ship.hold_size = 100
            ship.cargo_size = 0

        # Create a mock lot
        from unittest.mock import Mock
        mock_lot = Mock()
        mock_lot.mass = 5
        mock_lot.base_price = 1000

        # Set destination
        ship.set_course_for("Jae Tellona")

        # Mock _is_lot_profitable to return True (profitable)
        # and mock buy_cargo_lot to avoid actual purchase complexity
        with patch.object(agent, '_is_lot_profitable',
                          return_value=(True, 100)):
            with patch.object(ship, 'buy_cargo_lot') as mock_buy:
                purchased, mass = agent._try_purchase_lot(mock_lot)

                # Should call buy_cargo_lot with time and lot
                # (buy_cargo_lot now requires time parameter)
                self.assertTrue(purchased)
                self.assertEqual(mass, 5)
                # Verify it was called
                # (don't check exact args since time varies)
                mock_buy.assert_called_once()

    def test_format_cargo_message_with_skipped(self):
        """Test cargo loading message includes skipped count (line 698)."""
        sim = Simulation(self.game_state, num_ships=1, duration_days=1.0)
        sim.setup()
        agent = sim.agents[0]

        # Test with both loaded and skipped
        msg = agent._format_cargo_loading_message(2, 10, 3)
        self.assertIn("loaded 2 cargo lot", msg)
        self.assertIn("10t", msg)
        self.assertIn("skipped 3 unprofitable", msg)

        # Test with only skipped
        msg = agent._format_cargo_loading_message(0, 0, 5)
        self.assertIn("skipped 5 unprofitable", msg)
        self.assertNotIn("loaded", msg)

    def test_crew_profit_share_insufficient_funds(self):
        """Test crew profit share when ship can't afford it."""
        sim = Simulation(
            self.game_state,
            num_ships=1,
            duration_days=100.0,
            verbose=True,
            starting_capital=10_000  # Very low capital
        )
        sim.setup()

        agent = sim.agents[0]

        # Drain most funds using ship.debit
        agent.ship.debit(
            time=0,
            amount=9_500,
            memo="Drain funds"
        )

        # Set up maintenance scenario with high profit
        agent.ship.last_balance_at_maintenance = 100
        # Current balance is 500, so annual profit = 400
        # Crew share = 40 (10% of 400)
        # But let's drain even more so we can't afford it
        agent.ship.debit(
            time=0,
            amount=490,
            memo="Drain more funds"
        )
        # Now balance is 10, can't afford crew share of 40

        # Mock the environment time
        with patch.object(agent, 'env') as mock_env:
            mock_env.now = 0

            # Call _perform_maintenance which should trigger the broke path
            agent._perform_maintenance()

            # Ship should be marked as broke
            self.assertTrue(agent.broke)

    def test_verbose_payroll_reporting(self):
        """Test verbose mode payroll reporting."""
        sim = Simulation(
            self.game_state,
            num_ships=1,
            duration_days=30.0,
            verbose=True  # Enable verbose mode
        )
        sim.setup()

        agent = sim.agents[0]

        # Mock environment and calendar
        with patch.object(agent, 'env') as mock_env:
            mock_env.now = 2  # Day 2 (first month)

            # Call _process_monthly_payroll (correct method name)
            # This should trigger the verbose reporting path
            agent._process_monthly_payroll()

            # Verify payroll was processed (balance should decrease)
            self.assertLess(
                agent.ship.owner.balance,
                sim.starting_capital
            )


if __name__ == '__main__':
    unittest.main()
