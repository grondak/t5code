"""Demonstrate Trader skill predicting actual value ranges."""

from t5code import (
    T5Lot,
    load_and_parse_t5_map,
    load_and_parse_t5_ship_classes,
    T5World,
    find_best_broker,
)
from t5code.T5Tables import ACTUAL_VALUE


class GameState:
    """Game state container."""

    def __init__(self):
        raw_worlds = load_and_parse_t5_map("resources/t5_map.txt")
        self.world_data = T5World.load_all_worlds(raw_worlds)
        self.ship_data = load_and_parse_t5_ship_classes(
            "resources/t5_ship_classes.csv")


def demonstrate_trader_skill():
    """Show how Trader skill provides market prediction."""

    gs = GameState()
    origin = "Rhylanor"
    destination = "Jae Tellona"

    # Get broker info
    dest_world = gs.world_data[destination]
    starport = dest_world.get_starport()
    broker = find_best_broker(starport)
    broker_mod = broker.get("mod", 0)

    print("="*70)
    print("TRADER SKILL DEMONSTRATION")
    print("="*70)
    print()
    print(f"Selling goods at {destination}")
    print(f"Broker skill: {broker}")
    print()

    # Create a lot
    lot = T5Lot(origin, gs)
    lot.mass = 10

    base_value = lot.determine_sale_value_on(destination, gs)
    print(f"Lot: {lot.lot_id}")
    print(f"Base sale value: Cr {base_value:,}")
    print()

    # WITHOUT Trader skill - roll both dice at once
    print("="*70)
    print("WITHOUT TRADER SKILL (Regular Sale)")
    print("="*70)
    print("Rolling flux and checking actual value table...")
    actual_multiplier = lot.consult_actual_value_table(broker_mod)
    actual_value = base_value * actual_multiplier
    print(f"  Actual value multiplier: {actual_multiplier:.1%}")
    print(f"  Final sale price: Cr {actual_value:,.0f}")
    print()

    # WITH Trader skill - roll first die, see range, decide
    print("="*70)
    print("WITH TRADER SKILL (Predictive Sale)")
    print("="*70)
    print("Trader rolls first die to predict market...")

    # Use Trader skill to predict range
    min_mult, max_mult, flux = lot.predict_actual_value_range(broker_mod)

    print(f"  First die rolled: {flux.first_die}")
    print(f"  Flux range: {flux.potential_range}")
    print(f"  Price range: {min_mult:.1%} to {max_mult:.1%}")
    print(f"  Estimated value: Cr {base_value * min_mult:,.0f} "
          f"to Cr {base_value * max_mult:,.0f}")
    print()

    # Make decision based on prediction
    if min_mult >= 1.0:
        print("✓ DECISION: Excellent! Even worst case "
              "is at or above base price.")
        print("  → SELL NOW")
    elif min_mult >= 0.8:
        print("✓ DECISION: Acceptable. Minimum loss is small.")
        print("  → SELL NOW")
    else:
        print("✗ DECISION: Risky! Could lose significant money.")
        print("  → HOLD CARGO or try different market")
        print()
        return

    print()
    print("Rolling second die to finalize sale...")
    final_flux = flux.roll_second()

    # Look up final value
    clamped_flux = max(-5, min(8, final_flux + broker_mod))
    final_multiplier = ACTUAL_VALUE[clamped_flux]
    final_value = base_value * final_multiplier

    print(f"  Second die: {flux.second_die}")
    print(f"  Final flux: {final_flux:+d} "
          f"(+ {broker_mod} broker = {clamped_flux})")
    print(f"  Actual multiplier: {final_multiplier:.1%}")
    print(f"  FINAL SALE PRICE: Cr {final_value:,.0f}")
    print()

    # Show advantage of prediction
    profit_loss = final_value - base_value
    if profit_loss >= 0:
        print(f"  Profit: Cr {profit_loss:,.0f} "
              f"(+{profit_loss/base_value:.1%})")
    else:
        print(f"  Loss: Cr {profit_loss:,.0f} ({profit_loss/base_value:.1%})")
    print()
    print("="*70)


def show_all_scenarios():
    """Show all possible first die outcomes."""

    gs = GameState()
    origin = "Rhylanor"
    destination = "Jae Tellona"

    # Get broker
    dest_world = gs.world_data[destination]
    starport = dest_world.get_starport()
    broker = find_best_broker(starport)
    broker_mod = broker.get("mod", 0)

    lot = T5Lot(origin, gs)
    base_value = lot.determine_sale_value_on(destination, gs)

    print()
    print("="*70)
    print("ALL POSSIBLE TRADER PREDICTIONS")
    print("="*70)
    print(f"Base value: Cr {base_value:,}")
    print(f"Broker modifier: +{broker_mod}")
    print()
    print(f"{'First Die':<12} {'Flux Range':<15} "
          f"{'Multiplier Range':<20} {'Value Range'}")
    print("-"*70)

    from t5code.T5Basics import SequentialFlux

    for first_die in range(1, 7):
        flux = SequentialFlux(first_die=first_die)
        min_mult, max_mult, _ = lot.predict_actual_value_range(
            broker_mod, flux)
        min_val = base_value * min_mult
        max_val = base_value * max_mult

        print(f"{first_die:<12} {str(flux.potential_range):<15} "
              f"{min_mult:.1%} to {max_mult:.1%}  "
              f"Cr {min_val:>8,.0f} to {max_val:>8,.0f}")

    print("="*70)
    print()


if __name__ == "__main__":
    demonstrate_trader_skill()
    show_all_scenarios()
