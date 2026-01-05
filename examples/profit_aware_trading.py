"""Demonstrate profit-aware trade route selection.

Shows how ships evaluate potential destinations for cargo profitability
and make intelligent routing decisions.
"""

from t5code.GameState import GameState, load_and_parse_t5_map
from t5code.T5World import T5World
from t5code.T5ShipClass import T5ShipClass
from t5code.T5Starship import T5Starship
from t5code.T5Lot import T5Lot

# Load game data
MAP_FILE = "resources/t5_map.txt"
GameState.world_data = T5World.load_all_worlds(
    load_and_parse_t5_map(MAP_FILE))

# Create a merchant ship with Jump-3
merchant_data = {
    "class_name": "Far Trader",
    "jump_rating": 3,
    "maneuver_rating": 2,
    "cargo_capacity": 82,
    "staterooms": 10,
    "low_berths": 20,
}

ship_class = T5ShipClass("Far Trader", merchant_data)
ship = T5Starship("Merchant Princess", "Rhylanor", ship_class)

print("Profit-Aware Trade Route Selection")
print("=" * 70)
print()
print(f"Ship: {ship.ship_name}")
print(f"Location: {ship.location}")
print(f"Jump Rating: {ship.jump_rating}")
print()

# Show all worlds in range
print("Step 1: Find worlds within jump range")
print("-" * 70)
reachable = ship.get_worlds_in_jump_range(GameState)
print(f"Found {len(reachable)} worlds within Jump-{ship.jump_rating}:")
for world in sorted(reachable):
    print(f"  - {world}")
print()

# Show profitable destinations
print("Step 2: Evaluate cargo profitability")
print("-" * 70)
profitable = ship.find_profitable_destinations(GameState)

if profitable:
    print(f"Found {len(profitable)} profitable destinations:")
    print()
    for world_name, profit in profitable:
        world_obj = GameState.world_data[world_name]
        uwp = world_obj.world_data["UWP"]
        print(f"  {world_name:15} ({uwp})  Profit: +Cr{profit:>5}/ton")
else:
    print("No profitable destinations found")
print()

# Show unprofitable worlds
unprofitable = set(reachable) - {w for w, p in profitable}
if unprofitable:
    print(f"{len(unprofitable)} worlds with no profit opportunity:")
    for world in sorted(unprofitable):
        world_obj = GameState.world_data[world]
        uwp = world_obj.world_data["UWP"]
        print(f"  {world:15} ({uwp})")
    print()

# Demonstrate cargo evaluation
print("Step 3: Example cargo lot evaluation")
print("-" * 70)
sample_lot = T5Lot("Rhylanor", GameState)
sample_lot.mass = 10  # 10 ton lot
purchase_price = sample_lot.origin_value * sample_lot.mass

print(f"Sample cargo lot from {ship.location}:")
print(f"  Type: {sample_lot.lot_id}")
print(f"  Mass: {sample_lot.mass}t")
print(f"  Purchase price: Cr{purchase_price:,}")
print()

if profitable:
    best_dest, best_profit = profitable[0]
    sale_value_per_ton = sample_lot.determine_sale_value_on(best_dest,
                                                            GameState)
    sale_value_total = sale_value_per_ton * sample_lot.mass
    total_profit = sale_value_total - purchase_price

    print(f"Best destination: {best_dest}")
    print(f"  Sale value: Cr{sale_value_per_ton:,}/ton "
          f"(Cr{sale_value_total:,} total)")
    print(f"  Profit: Cr{total_profit:,} ({best_profit}/ton)")
    print()

    if len(profitable) > 1:
        worst_dest, worst_profit = profitable[-1]
        sale_value_per_ton = sample_lot.determine_sale_value_on(worst_dest,
                                                                GameState)
        sale_value_total = sale_value_per_ton * sample_lot.mass
        total_profit = sale_value_total - purchase_price

        print(f"Least profitable destination: {worst_dest}")
        print(f"  Sale value: Cr{sale_value_per_ton:,}/ton "
              f"(Cr{sale_value_total:,} total)")
        print(f"  Profit: Cr{total_profit:,} ({worst_profit}/ton)")
        print()

if unprofitable:
    unprofitable_world = sorted(unprofitable)[0]
    sale_value_per_ton = sample_lot.determine_sale_value_on(unprofitable_world,
                                                            GameState)
    sale_value_total = sale_value_per_ton * sample_lot.mass
    total_profit = sale_value_total - purchase_price

    print(f"Unprofitable destination example: {unprofitable_world}")
    print(f"  Sale value: Cr{sale_value_per_ton:,}/ton "
          f"(Cr{sale_value_total:,} total)")
    print(f"  Profit/Loss: Cr{total_profit:,}")
    print()

# Summary
print("Decision Logic:")
print("-" * 70)
print(f"Ship will prefer destinations from the {len(profitable)} "
      "profitable worlds")
print("Ship will skip cargo that would result in losses")
if unprofitable:
    print(f"Ship will travel to {len(unprofitable)} "
          "unprofitable worlds only if needed")
print("This creates realistic merchant behavior seeking profit opportunities")
