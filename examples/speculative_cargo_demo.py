"""Demonstration of speculative cargo generation for Traveller 5.

In Traveller, captains often need to leave a world "soon" rather than
waiting many days for freight to accumulate. This demo shows how a captain
can purchase up to 100 tons of speculative cargo in lots of up to 10 tons.
"""

from t5code import (
    T5World,
    load_and_parse_t5_map,
)


class SimpleGameState:
    """Minimal GameState for speculative cargo demo."""

    def __init__(self, map_file: str = "resources/t5_map.txt"):
        raw_worlds = load_and_parse_t5_map(map_file)
        self.world_data = T5World.load_all_worlds(raw_worlds)


def main():
    # Initialize game state
    gs = SimpleGameState()

    # Captain is at Rhylanor and needs cargo fast
    world = gs.world_data["Rhylanor"]

    print("=" * 70)
    print("SPECULATIVE CARGO MARKET at Rhylanor")
    print("=" * 70)
    print(f"World: {world.name}")
    print(f"UWP: {world.uwp()}")
    print(f"Trade Classifications: {world.trade_classifications()}")
    print(f"Starport: Class {world.get_starport()}")
    print()

    # Generate available speculative cargo
    print("Generating available speculative cargo lots...")
    lots = world.generate_speculative_cargo(gs)

    print(f"\nAvailable: {len(lots)} lots totaling "
          f"{sum(lot.mass for lot in lots)} tons")
    print()
    print(f"{'Lot #':<8} {'Mass':<8} {'Value/ton':<12} {'Total Value':<15} "
          f"{'Goods ID'}")
    print("-" * 70)

    for i, lot in enumerate(lots, 1):
        value_per_ton = lot.origin_value
        total_value = lot.origin_value * lot.mass
        print(f"{i:<8} {lot.mass:<8} Cr{value_per_ton:<10,} "
              f"Cr{total_value:<13,} "
              f"{lot.lot_id}")

    print("-" * 70)
    total_investment = sum(lot.origin_value * lot.mass for lot in lots)
    print(f"Total investment for all lots: Cr{total_investment:,}")
    print()

    # Simulate captain with limited cargo space
    print("=" * 70)
    print("CAPTAIN'S PURCHASE SCENARIO")
    print("=" * 70)
    ship_cargo_capacity = 82  # Typical merchant ship
    print(f"Ship cargo capacity: {ship_cargo_capacity} tons")
    print()

    purchased_lots = []
    total_purchased_mass = 0
    total_cost = 0

    for lot in lots:
        if total_purchased_mass + lot.mass <= ship_cargo_capacity:
            purchased_lots.append(lot)
            total_purchased_mass += lot.mass
            total_cost += lot.origin_value * lot.mass

    print(f"Purchased {len(purchased_lots)} lots:")
    for i, lot in enumerate(purchased_lots, 1):
        cost = lot.origin_value * lot.mass
        print(f"  {i}. {lot.mass} tons @ Cr{lot.origin_value:,}/ton = "
              f"Cr{cost:,}")

    print()
    print(f"Total purchased: {total_purchased_mass} tons")
    print(f"Total cost: Cr{total_cost:,}")
    print(
        f"Remaining capacity: {ship_cargo_capacity - total_purchased_mass} "
        "tons")
    print()

    remaining_lots = len(lots) - len(purchased_lots)
    if remaining_lots > 0:
        print(f"Left {remaining_lots} lots on the market (insufficient space)")

    print()
    print("The captain can now depart immediately.")


if __name__ == "__main__":
    main()
