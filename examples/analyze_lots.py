"""Analyze potential profit for 5 random lots."""

from t5code import (
    T5Lot,
    T5Starship,
    load_and_parse_t5_map,
    load_and_parse_t5_ship_classes,
    T5World,
    T5ShipClass,
)


class GameState:
    """Simple game state container."""
    def __init__(self, map_file: str, ship_classes_file: str):
        raw_worlds = load_and_parse_t5_map(map_file)
        raw_ships = load_and_parse_t5_ship_classes(ship_classes_file)
        self.world_data = T5World.load_all_worlds(raw_worlds)
        self.ship_data = T5ShipClass.load_all_ship_classes(raw_ships)


def analyze_lot_profit(origin: str, destination: str, num_lots: int = 5):
    """Generate random lots and calculate potential profit."""

    # Load game data
    gs = GameState("resources/t5_map.txt", "resources/t5_ship_classes.csv")

    # Create a ship for reference
    ship_class = next(iter(gs.ship_data.values()))
    ship = T5Starship("Profit Analyzer", origin, ship_class)
    ship.set_course_for(destination)

    print(f"\n{'='*70}")
    print(f"PROFIT ANALYSIS: {origin} → {destination}")
    print(f"{'='*70}\n")

    total_cost = 0.0
    total_revenue = 0.0
    lots = []

    # Generate random lots
    for i in range(num_lots):
        lot = T5Lot(origin, gs)
        lot.mass = 10  # 10 tons each

        try:
            # Get purchase cost and sale value
            purchase_cost = lot.origin_value * lot.mass
            sale_value = (lot.determine_sale_value_on(destination, gs)
                          * lot.mass)
            profit = sale_value - purchase_cost
            profit_pct = ((profit / purchase_cost * 100)
                          if purchase_cost > 0 else 0)
        except KeyError as e:
            # Some world classifications may not have trade effects defined
            print(f"Lot {i+1}: {lot.lot_id}")
            print(f"  ⚠ Cannot calculate sale value "
                  f"(unsupported classification: {e})")

            print()
            continue

        lots.append({
            'lot': lot,
            'cost': purchase_cost,
            'revenue': sale_value,
            'profit': profit,
            'profit_pct': profit_pct
        })

        total_cost += purchase_cost
        total_revenue += sale_value

        print(f"Lot {i+1}: {lot.lot_id}")
        print(f"  Purchase Cost:  Cr {purchase_cost:>12,.2f}")
        print(f"  Sale Value:     Cr {sale_value:>12,.2f}")
        print(f"  Profit:         Cr {profit:>12,.2f} ({profit_pct:>6.1f}%)")
        print()

    # Summary
    total_profit = total_revenue - total_cost
    avg_profit_pct = (total_profit / total_cost * 100) if total_cost > 0 else 0

    print(f"{'-'*70}")
    print("SUMMARY:")
    print(f"  Total Investment:  Cr {total_cost:>12,.2f}")
    print(f"  Total Revenue:     Cr {total_revenue:>12,.2f}")
    print("  Total Profit:      Cr "
          f"{total_profit:>12,.2f} ({avg_profit_pct:>6.1f}%)")
    print(f"{'='*70}\n")

    # Find best and worst lots (if any valid lots)
    if lots:
        best = max(lots, key=lambda x: x['profit_pct'])
        worst = min(lots, key=lambda x: x['profit_pct'])

        print(f"Best Lot:  {best['lot'].lot_id} "
              f"({best['profit_pct']:.1f}% profit)")

        print(f"Worst Lot: {worst['lot'].lot_id} "
              f"({worst['profit_pct']:.1f}% profit)")
    else:
        print("No valid lots to analyze "
              "(all encountered unsupported classifications)")
    print()


if __name__ == "__main__":
    # Example: Analyze lots from different routes
    print("\n" + "="*70)
    print("TRADE ROUTE PROFIT ANALYZER")
    print("="*70)

    routes = [
        ("Rhylanor", "Jae Tellona"),
        ("Jae Tellona", "Rhylanor"),
    ]

    for origin, destination in routes:
        analyze_lot_profit(origin, destination, num_lots=5)
        print()
