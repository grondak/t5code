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
        """Test _load_cargo handles InsufficientFundsError.

        Verifies that the exception handler catches
        InsufficientFundsError during cargo purchase and breaks
        the loop appropriately.
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
            # Make ship have space
            original_cargo_size = ship.cargo_size
            ship.cargo_size = 0

            # First lot succeeds, second raises exception
            call_count = 0

            def side_effect_purchase(*args):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return (True, 10)  # First succeeds
                else:
                    # Second raises exception
                    raise InsufficientFundsError("Not enough funds")

            with patch.object(
                agent,
                '_try_purchase_lot',
                side_effect=side_effect_purchase
            ):
                # Call _load_cargo
                agent._load_cargo()

            # Should have tried to purchase both lots
            self.assertEqual(call_count, 2)
        finally:
            # Restore original world and cargo size
            if original_world:
                sim.game_state.world_data[ship.location] = (
                    original_world
                )
            ship.cargo_size = original_cargo_size

    def test_load_cargo_capacity_exceeded_exception(self):
        """Test _load_cargo handles CapacityExceededError.

        Verifies that the exception handler catches
        CapacityExceededError during cargo purchase and breaks
        the loop at line 623.
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
            # Make ship have space
            original_cargo_size = ship.cargo_size
            ship.cargo_size = 0

            # First lot succeeds, second raises exception
            call_count = 0

            def side_effect_purchase(*args):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return (True, 10)  # First succeeds
                else:
                    # Second raises exception (line 622)
                    raise CapacityExceededError("Not enough space")

            with patch.object(
                agent,
                '_try_purchase_lot',
                side_effect=side_effect_purchase
            ):
                # Call _load_cargo
                agent._load_cargo()

            # Should have tried to purchase both lots and hit
            # the break at line 623
            self.assertEqual(call_count, 2)
        finally:
            # Restore original world and cargo size
            if original_world:
                sim.game_state.world_data[ship.location] = (
                    original_world
                )
            ship.cargo_size = original_cargo_size

    def test_load_cargo_exception_with_verbose(self):
        """Test _load_cargo exception handling with verbose mode.

        This ensures line 623 (break after exception) is executed,
        followed by verbose message reporting at lines 625-630.
        """
        # Setup simulation with verbose mode
        sim = Simulation(
            self.game_state,
            num_ships=1,
            duration_days=1.0,
            verbose=True
        )
        sim.setup()

        agent = sim.agents[0]
        ship = agent.ship

        # Mock world with lots
        mock_world = Mock()
        mock_lot1 = Mock()
        mock_lot2 = Mock()
        mock_lot3 = Mock()
        # Need more lots to ensure we hit the exception after
        # loading some cargo
        mock_world.generate_speculative_cargo.return_value = [
            mock_lot1,
            mock_lot2,
            mock_lot3
        ]

        # Temporarily replace the world in game_state
        original_world = sim.game_state.world_data.get(ship.location)
        sim.game_state.world_data[ship.location] = mock_world

        try:
            # Make ship have space
            original_cargo_size = ship.cargo_size
            ship.cargo_size = 0

            # First lot succeeds, second succeeds, third raises
            call_count = 0

            def side_effect_purchase(*args):
                nonlocal call_count
                call_count += 1
                if call_count < 3:
                    return (True, 10)  # First two succeed
                else:
                    # This should trigger the exception handler
                    # and break at line 623
                    raise InsufficientFundsError("Not enough funds")

            with patch.object(
                agent,
                '_try_purchase_lot',
                side_effect=side_effect_purchase
            ):
                # Call _load_cargo - should hit exception,
                # break at line 623, then check verbose at line 625
                # and report status
                agent._load_cargo()

            # Should have tried to purchase three lots and stopped
            # at the exception
            self.assertEqual(call_count, 3)
        finally:
            # Restore original world and cargo size
            if original_world:
                sim.game_state.world_data[ship.location] = (
                    original_world
                )
            ship.cargo_size = original_cargo_size

    def test_sell_cargo_exception_handling(self):
        """Test _sell_cargo handles exceptions during sale.

        Verifies that the exception handler at lines 430-436
        catches general exceptions during cargo sale and prints
        an error message without crashing.
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
                # Call _sell_cargo - should catch exception at
                # line 430 and print error at line 436
                agent._sell_cargo()

                # Verify error was printed
                mock_print.assert_called_once()
                call_args = mock_print.call_args[0][0]
                self.assertIn("Sale error", call_args)
                self.assertIn("Test exception in sale", call_args)

        # Clean up - remove the lot
        ship.cargo_manifest["cargo"] = []

    def test_sell_cargo_verbose_success(self):
        """Test _sell_cargo with verbose reporting on success.

        Verifies that lines 435-436 (verbose status report)
        are covered when selling cargo successfully.
        """
        # Setup simulation with verbose mode
        sim = Simulation(
            self.game_state,
            num_ships=1,
            duration_days=1.0,
            verbose=True
        )
        sim.setup()

        agent = sim.agents[0]
        ship = agent.ship

        # Create a cargo lot
        from t5code import T5Lot

        try:
            lot = T5Lot(ship.location, sim.game_state)
        except Exception:
            self.skipTest("Could not create lot at ship location")

        # Add lot to ship's cargo manifest
        if "cargo" not in ship.cargo_manifest:
            ship.cargo_manifest["cargo"] = []
        ship.cargo_manifest["cargo"].append(lot)

        # Mock sell_cargo_lot to return success
        mock_result = {
            "profit": 5000,
            "sale_price": 15000,
            "purchase_price": 10000
        }

        with patch.object(
            ship,
            'sell_cargo_lot',
            return_value=mock_result
        ):
            # Call _sell_cargo - should hit lines 430-436
            # including verbose reporting
            agent._sell_cargo()

        # Note: sell_cargo_lot was mocked, so the lot wasn't
        # actually removed, but the code path was executed


if __name__ == '__main__':
    unittest.main()
