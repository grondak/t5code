"""Simple script to analyze 5 random lots for profit potential.

Usage:
    python simple_lot_analysis.py

Edit the ORIGIN and DESTINATION variables below to analyze different routes.
"""

from t5code import (
    T5Lot,
    T5Starship,
    load_and_parse_t5_map,
    load_and_parse_t5_ship_classes,
    T5World,
    T5ShipClass,
)

# ============================================================================
# CONFIGURATION - Edit these values
# ============================================================================
ORIGIN = "Rhylanor"
DESTINATION = "Jae Tellona"
NUM_LOTS = 5
LOT_SIZE_TONS = 10
# ============================================================================


class GameState:
    """Game state container."""
    def __init__(self):
        raw_worlds = load_and_parse_t5_map("resources/t5_map.txt")
        raw_ships = load_and_parse_t5_ship_classes(
            "resources/t5_ship_classes.csv")
        self.world_data = T5World.load_all_worlds(raw_worlds)
        self.ship_data = T5ShipClass.load_all_ship_classes(raw_ships)


def main():
    """Analyze random lots for profit potential."""

    # Load game data
    print("Loading game data...")
    gs = GameState()

    # Create ship with destination
    ship_class = next(iter(gs.ship_data.values()))
    ship = T5Starship("Analysis Ship", ORIGIN, ship_class)
    ship.set_course_for(DESTINATION)

    print(f"\n{'='*70}")
    print("  TRADE LOT PROFIT ANALYSIS")
    print(f"  Route: {ORIGIN} → {DESTINATION}")
    print(f"  Analyzing {NUM_LOTS} lots of {LOT_SIZE_TONS} tons each")
    print(f"{'='*70}\n")

    total_cost = 0
    total_revenue = 0
    successful_lots = 0

    # Generate and analyze lots
    for i in range(1, NUM_LOTS + 1):
        lot = T5Lot(ORIGIN, gs)
        lot.mass = LOT_SIZE_TONS

        try:
            purchase_cost = lot.origin_value * lot.mass
            sale_value = (lot.determine_sale_value_on(DESTINATION, gs)
                          * lot.mass)
            profit = sale_value - purchase_cost
            profit_pct = ((profit / purchase_cost * 100)
                          if purchase_cost > 0 else 0)

            print(f"Lot {i}: {lot.lot_id}")
            print(f"  Buy:   Cr {purchase_cost:>10,.0f}")
            print(f"  Sell:  Cr {sale_value:>10,.0f}")
            print(f"  Profit: Cr {profit:>10,.0f} ({profit_pct:+.1f}%)")
            print()

            total_cost += purchase_cost
            total_revenue += sale_value
            successful_lots += 1

        except KeyError as e:
            print(f"Lot {i}: {lot.lot_id}")
            print(f"  ⚠ Cannot price (unsupported classification: {e})")
            print()

    # Summary
    if successful_lots > 0:
        total_profit = total_revenue - total_cost
        roi = (total_profit / total_cost * 100) if total_cost > 0 else 0

        print(f"{'-'*70}")
        print(f"SUMMARY ({successful_lots}/{NUM_LOTS} lots priced):")
        print(f"  Total Investment:  Cr {total_cost:>12,.0f}")
        print(f"  Total Revenue:     Cr {total_revenue:>12,.0f}")
        print(f"  Total Profit:      Cr {total_profit:>12,.0f}")
        print(f"  Return on Investment: {roi:+.1f}%")
        print(f"{'='*70}\n")

        if roi > 0:
            print("✓ This route is PROFITABLE")
        else:
            print("✗ This route is UNPROFITABLE - try the reverse direction!")
    else:
        print("✗ No lots could be priced (unsupported world classifications)")
        print("  Try a different route")
    print()


if __name__ == "__main__":
    main()
