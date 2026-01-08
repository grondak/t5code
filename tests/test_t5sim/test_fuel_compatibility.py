"""Test fuel compatibility logic for ship spawning."""

import pytest
from t5code import GameState as gs_module, T5World, T5ShipClass
from t5code.GameState import GameState
from t5sim import Simulation


@pytest.fixture
def game_state_with_starports():
    """Create game state with worlds having different starport types."""
    gs = GameState()

    # Create mock worlds with different starport types
    # A/B ports have both refined and unrefined fuel
    # C/D ports have only unrefined fuel
    # E/X ports have no fuel

    raw_worlds = {
        "TestWorldA": {
            "Name": "TestWorldA",
            "Sector": "Test",
            "UWP": "A123456-7",  # A starport
            "Hex": "0101",
            "Subsector": "A",
            "Coordinates": (1, 1),
            "Zone": "",
            "TradeClassifications": "",
            "Importance": "{0}",
        },
        "TestWorldB": {
            "Name": "TestWorldB",
            "Sector": "Test",
            "UWP": "B234567-8",  # B starport
            "Hex": "0102",
            "Subsector": "A",
            "Coordinates": (1, 2),
            "Zone": "",
            "TradeClassifications": "",
            "Importance": "{0}",
        },
        "TestWorldC": {
            "Name": "TestWorldC",
            "Sector": "Test",
            "UWP": "C345678-9",  # C starport
            "Hex": "0103",
            "Subsector": "A",
            "Coordinates": (1, 3),
            "Zone": "",
            "TradeClassifications": "",
            "Importance": "{0}",
        },
        "TestWorldD": {
            "Name": "TestWorldD",
            "Sector": "Test",
            "UWP": "D456789-A",  # D starport
            "Hex": "0104",
            "Subsector": "A",
            "Coordinates": (1, 4),
            "Zone": "",
            "TradeClassifications": "",
            "Importance": "{0}",
        },
    }

    gs.world_data = T5World.load_all_worlds(raw_worlds)

    # Create ship classes with different fuel refining capabilities
    gs.ship_classes = {
        "ShipCanRefine": {
            "class_name": "ShipCanRefine",
            "ship_cost": 1000000.0,
            "jump_rating": 2,
            "maneuver_rating": 1,
            "powerplant_rating": 2,
            "cargo_capacity": 82,
            "staterooms": 10,
            "low_berths": 20,
            "crew_positions": [],
            "jump_fuel_capacity": 40,
            "ops_fuel_capacity": 10,
            "role": "civilian",
            "frequency": 1.0,
            "can_refine_fuel": True,
        },
        "ShipCannotRefine": {
            "class_name": "ShipCannotRefine",
            "ship_cost": 1000000.0,
            "jump_rating": 2,
            "maneuver_rating": 1,
            "powerplant_rating": 2,
            "cargo_capacity": 82,
            "staterooms": 10,
            "low_berths": 20,
            "crew_positions": [],
            "jump_fuel_capacity": 40,
            "ops_fuel_capacity": 10,
            "role": "civilian",
            "frequency": 1.0,
            "can_refine_fuel": False,
        },
    }

    return gs


def test_ship_cannot_refine_needs_refined_fuel_starports(
    game_state_with_starports,
):
    """Ships that can't refine fuel should only spawn at A/B starports.

    Ships without fuel processors cannot refine unrefined fuel themselves,
    so they need refined fuel from the starport.
    A and B starports provide refined fuel.
    """
    gs = game_state_with_starports
    sim = Simulation(gs, num_ships=1, duration_days=10.0)

    # Get the ship class that cannot refine
    ship_class_dict = gs.ship_classes["ShipCannotRefine"]
    ship_class = T5ShipClass("ShipCannotRefine", ship_class_dict)

    # Find starting world multiple times to test the logic
    worlds = list(gs.world_data.keys())

    # Run the test multiple times to ensure consistency
    for _ in range(20):
        starting_world, _ = sim._find_starting_world(ship_class, worlds)

        world_obj = gs.world_data[starting_world]
        starport_type = world_obj.get_starport()

        # Ships that cannot refine should spawn at A or B starports
        # (which have refined fuel available)
        # Note: In our test data, all worlds are reachable, so we should
        # always get A or B
        assert starport_type in ["A", "B"], (
            f"Ship that cannot refine fuel spawned at {starport_type} "
            f"starport ({starting_world}), but should only spawn at "
            f"A or B starports with refined fuel"
        )


def test_ship_can_refine_spawns_anywhere(game_state_with_starports):
    """Ships that can refine fuel should be able to spawn at any starport."""
    gs = game_state_with_starports
    sim = Simulation(gs, num_ships=1, duration_days=10.0)

    # Get the ship class that can refine
    ship_class_dict = gs.ship_classes["ShipCanRefine"]
    ship_class = T5ShipClass("ShipCanRefine", ship_class_dict)

    worlds = list(gs.world_data.keys())

    # Track which starport types we see
    starport_types_seen = set()

    # Run multiple times to see variety
    for _ in range(50):
        starting_world, _ = sim._find_starting_world(ship_class, worlds)
        world_obj = gs.world_data[starting_world]
        starport_type = world_obj.get_starport()
        starport_types_seen.add(starport_type)

    # Ships that can refine should be able to spawn at any starport
    # We should see a variety of starport types over 50 iterations
    assert len(starport_types_seen) > 1, (
        "Ship that can refine fuel should spawn at various starports"
    )


def test_fuel_compatibility_with_real_data():
    """Test fuel compatibility with real game data."""
    gs = GameState()
    raw_worlds = gs_module.load_and_parse_t5_map("resources/t5_map.txt")
    raw_ships = gs_module.load_and_parse_t5_ship_classes(
        "resources/t5_ship_classes.csv"
    )
    gs.world_data = T5World.load_all_worlds(raw_worlds)
    gs.ship_classes = raw_ships

    sim = Simulation(gs, num_ships=1, duration_days=10.0)

    # Find ships that cannot refine fuel
    ships_cannot_refine = [
        (name, data)
        for name, data in gs.ship_classes.items()
        if not data.get("can_refine_fuel", False)
    ]

    if ships_cannot_refine:
        # Test with a ship that cannot refine
        ship_name, ship_data = ships_cannot_refine[0]
        ship_class = T5ShipClass(ship_name, ship_data)

        worlds = list(gs.world_data.keys())

        # Try finding starting world multiple times
        for _ in range(10):
            starting_world, reachable = sim._find_starting_world(
                ship_class, worlds
            )

            world_obj = gs.world_data[starting_world]
            starport_type = world_obj.get_starport()

            # Check STARPORT_TYPES to see what fuel is available
            from t5code.T5Tables import STARPORT_TYPES
            starport_info = STARPORT_TYPES.get(starport_type, {})
            has_refined = starport_info.get("RefinedFuel", False)

            # If ship cannot refine, it must spawn at a port with refined fuel
            assert has_refined or not reachable, (
                f"Ship {ship_name} (cannot refine fuel) spawned at "
                f"{starport_type} starport ({starting_world}) which lacks "
                f"refined fuel. Starport info: {starport_info}"
            )
