"""Demonstrate jump range calculation for ships.

Shows which worlds are reachable from a given starting location
based on ship jump drive capability.
"""

from t5code.GameState import GameState, load_and_parse_t5_map
from t5code.T5World import T5World
from t5code.T5ShipClass import T5ShipClass
from t5code.T5Starship import T5Starship

# Load game data
MAP_FILE = "resources/t5_map.txt"
GameState.world_data = T5World.load_all_worlds(
    load_and_parse_t5_map(MAP_FILE))

# Create a couple of ships with different jump capabilities
jump1_data = {
    "class_name": "Scout",
    "jump_rating": 1,
    "maneuver_rating": 2,
    "cargo_capacity": 20,
    "staterooms": 4,
    "low_berths": 0,
}

jump3_data = {
    "class_name": "Merchant",
    "jump_rating": 3,
    "maneuver_rating": 2,
    "cargo_capacity": 82,
    "staterooms": 10,
    "low_berths": 20,
}

scout_class = T5ShipClass("Scout", jump1_data)
merchant_class = T5ShipClass("Merchant", jump3_data)

# Create ships at Rhylanor
scout = T5Starship("Free Trader", "Rhylanor", scout_class)
merchant = T5Starship("Far Trader", "Rhylanor", merchant_class)

print("Jump Range Demonstration")
print("=" * 60)
print()
print("Starting Location: Rhylanor")
print()

# Show Jump-1 range
print(f"{scout.ship_name} ({scout.ship_class}, Jump-{scout.jump_rating})")
print("-" * 60)
jump1_worlds = scout.get_worlds_in_jump_range(GameState)
if jump1_worlds:
    print(f"Can reach {len(jump1_worlds)} worlds:")
    for world in sorted(jump1_worlds):
        world_obj = GameState.world_data[world]
        uwp = world_obj.world_data["UWP"]
        print(f"  - {world} ({uwp})")
else:
    print("  No worlds within jump range")
print()

# Show Jump-3 range
print(f"{merchant.ship_name} ({merchant.ship_class}, "
      f"Jump-{merchant.jump_rating})")
print("-" * 60)
jump3_worlds = merchant.get_worlds_in_jump_range(GameState)
if jump3_worlds:
    print(f"Can reach {len(jump3_worlds)} worlds:")
    for world in sorted(jump3_worlds):
        world_obj = GameState.world_data[world]
        uwp = world_obj.world_data["UWP"]
        print(f"  - {world} ({uwp})")
else:
    print("  No worlds within jump range")
print()

# Show the difference
only_jump3 = set(jump3_worlds) - set(jump1_worlds)
if only_jump3:
    print("Worlds only reachable with Jump-3 (not Jump-1):")
    print("-" * 60)
    for world in sorted(only_jump3):
        world_obj = GameState.world_data[world]
        uwp = world_obj.world_data["UWP"]
        print(f"  - {world} ({uwp})")
