"""Example driver for exercising small parts of the t5code package.

This module provides a simple, runnable example. It intentionally keeps
behavior procedural, but uses an instance `GameDriver` rather than a
class-used-as-namespace.
"""

from t5code import (
    T5Lot,
    T5Mail,
    T5NPC,
    T5ShipClass,
    T5Starship,
    T5World,
    find_best_broker,
    load_and_parse_t5_map,
    load_and_parse_t5_ship_classes,
)

MAP_FILE = "resources/t5_map.txt"
SHIP_CLASSES_FILE = "resources/t5_ship_classes.csv"


class GameDriver:
    """Container for game data used by the example runner."""

    def __init__(self, map_file: str = MAP_FILE,
                 ship_classes_file: str = SHIP_CLASSES_FILE):
        raw_worlds = load_and_parse_t5_map(map_file)
        raw_ships = load_and_parse_t5_ship_classes(ship_classes_file)
        self.world_data = T5World.load_all_worlds(raw_worlds)
        self.ship_data = T5ShipClass.load_all_ship_classes(raw_ships)


def setup_departure(origin: str, gd: GameDriver) -> T5Starship:
    """Load ship with crew, passengers, lots, and mail at origin."""
    freight_lot = T5Lot(origin, gd)
    freight_lot.mass = 10
    cargo_lot = T5Lot(origin, gd)
    cargo_lot.mass = 3

    npc_high = T5NPC("Admiral Miller")
    npc_mid = T5NPC("Colonel Mustard")
    npc_low = T5NPC("Civilian Joe")

    medic = T5NPC("Dr. Bones")
    medic.set_skill("medic", 5)

    trader = T5NPC("Merchant Marcus")
    trader.set_skill("trader", 4)

    ship_class = gd.ship_data.get("Freighter") or next(
        iter(gd.ship_data.values()))
    ship = T5Starship("Paprika", origin, ship_class)
    ship.hire_crew("medic", medic)
    ship.hire_crew("crew1", trader)
    ship.onload_passenger(npc_high, "high")
    ship.onload_passenger(npc_mid, "mid")
    ship.onload_passenger(npc_low, "low")
    ship.onload_lot(freight_lot, "freight")
    ship.onload_lot(cargo_lot, "cargo")
    ship.onload_mail(T5Mail(origin, "Jae Tellona", gd))

    return ship


def perform_arrival(ship: T5Starship) -> None:
    """Offload passengers and mail at destination."""
    for p in ship.offload_passengers("high"):
        print(f"Offloaded high passenger: {p.character_name}")
    print("Offloaded mail.")
    ship.offload_mail()
    print(f"Mail locker now has {len(ship.get_mail())} bundles")
    for p in ship.offload_passengers("mid"):
        print(f"Offloaded mid passenger: {p.character_name}")
    offload_freight(ship)
    for p in ship.offload_passengers("low"):
        print(f"Offloaded low passenger: {p.character_name}")


def _get_trader_prediction(lot, broker_mod: int):
    """Use Trader skill to predict market and get multiplier."""

    min_mult, max_mult, flux = lot.predict_actual_value_range(broker_mod)

    print(f"\nMerchant Marcus checks market for lot {lot.serial}:")
    print(f"  First die: {flux.first_die}")
    print(f"  Predicted range: {min_mult:.1%} to {max_mult:.1%}")

    return min_mult, max_mult, flux


def _evaluate_market_conditions(
        min_mult: float,
        max_mult: float,
        value: float):
    """Print market evaluation based on predicted multiplier range."""
    print(f"  Value estimate: Cr{value * min_mult:,.0f} "
          f"to Cr{value * max_mult:,.0f}")

    if min_mult >= 1.0:
        print("  Good market! Selling now.")
    elif min_mult >= 0.8:
        print("  Acceptable. Proceeding with sale.")
    else:
        print(f"  Poor market (risk of {(1-min_mult)*100:.0f}% loss).")
        print("  Selling anyway (no storage).")


def _complete_trader_roll(flux, broker_mod: int) -> float:
    """Complete the flux roll and return final multiplier."""
    from t5code.T5Tables import ACTUAL_VALUE

    final_flux = flux.roll_second()
    clamped = max(-5, min(8, final_flux + broker_mod))
    modifier = ACTUAL_VALUE[clamped]
    print(
        f"  Second die: {flux.second_die} → Final multiplier: {modifier:.1%}")

    return modifier


def _calculate_sale_proceeds(lot, value: float, modifier: float,
                             broker_rate: float):
    """Calculate actual sale value, fees, and profit."""
    actual = value * modifier
    fee = actual * broker_rate
    final = actual - fee
    purchase_cost = lot.origin_value * lot.mass
    profit = final - purchase_cost

    return final, fee, profit, purchase_cost


def _print_sale_summary(lot, final: float, fee: float, profit: float,
                        purchase_cost: float):
    """Print sale transaction summary."""
    print(f"Sold cargo lot {lot.serial} for Cr{final:,.2f} (fee Cr{fee:,.2f})")
    print(
        f"  Profit: Cr{profit:,.2f} ({(profit/purchase_cost)*100:+.1f}% ROI)")


def _print_trader_benefit_analysis(trader_skill: int, total_profit: float):
    """Print comprehensive Trader skill benefit analysis."""
    print(f"\n{'='*60}")
    print("TRADER SKILL BENEFIT ANALYSIS")
    print(f"{'='*60}")
    print(
        f"Merchant Marcus (Trader-{trader_skill}) "
        "provided market intelligence")
    print("that enabled informed decision-making. The early die roll showed")
    print("market conditions BEFORE committing to the sale.")
    print(f"\nTotal cargo result this sale: Cr{total_profit:,.2f}")

    if total_profit > 0:
        print("\nThe prediction showed favorable odds and paid off!")
    else:
        print("\nEven with a loss, Marcus showed the risk BEFORE selling.")
        print("Without Trader skill, this would have been a blind gamble.")
        print("The skill's value is preventing WORSE losses by revealing")
        print("risk levels before commitment.")

    print("\nKey Value: RISK MANAGEMENT - seeing the first die lets captains")
    print("hold cargo when markets are terrible (< 0.8x) and sell when")
    print("conditions are acceptable or good. This prevents catastrophic")
    print("losses over time.")
    print(f"{'='*60}")


def sell_cargo(ship: T5Starship, gd: GameDriver) -> None:
    """Sell all cargo items through the best broker, "
    "using Trader skill if available."""
    # Get broker information
    world = gd.world_data.get(ship.location)
    broker = (find_best_broker(world.get_starport()) if world
              else {"mod": 0, "rate": 0.0})

    # Check for trader in crew
    trader = ship.crew.get("crew1")
    has_trader = trader and trader.get_skill("trader") > 0
    trader_skill = trader.get_skill("trader") if has_trader else 0

    # Process each cargo lot
    total_profit = 0.0
    for lot in ship.get_cargo().get("cargo", []):
        value = lot.determine_sale_value_on(ship.location, gd)

        # Get price multiplier (with or without Trader skill)
        if has_trader:
            min_mult, max_mult, flux = _get_trader_prediction(
                lot, broker.get("mod", 0)
            )
            _evaluate_market_conditions(min_mult, max_mult, value)
            modifier = _complete_trader_roll(flux, broker.get("mod", 0))
        else:
            modifier = lot.consult_actual_value_table(broker.get("mod", 0))

        # Calculate and execute sale
        final, fee, profit, purchase_cost = _calculate_sale_proceeds(
            lot, value, modifier, broker.get("rate", 0.0)
        )
        total_profit += profit

        ship.credit(final)
        ship.offload_lot(lot.serial, "cargo")
        _print_sale_summary(lot, final, fee, profit, purchase_cost)

    # Show Trader skill benefit analysis
    if has_trader:
        _print_trader_benefit_analysis(trader_skill, total_profit)


def offload_freight(ship: T5Starship) -> None:
    """Offload all freight without selling."""
    for lot in ship.get_cargo().get("freight", []):
        ship.offload_lot(lot.serial, "freight")
        print(f"Offloaded freight lot {lot.serial} of {lot.mass} tons")


def _get_liaison_skill(ship: T5Starship) -> int:
    """Safely retrieve the Liaison skill from crew."""
    try:
        return ship.best_crew_skill["Liaison"]
    except (KeyError, AttributeError):
        return 0


def _try_onload_freight_lot(ship: T5Starship, lot: T5Lot) -> bool:
    """Attempt to load a freight lot.
    Return False if hold is too small (stop searching)."""
    try:
        ship.onload_lot(lot, "freight")
        ship.credit(1000 * lot.mass)
        return True
    except ValueError as e:
        if "Lot will not fit" in str(e):
            print(f"Rejecting lot because {lot.mass} is too big for the ship.")
            return False
        raise


def _report_hold_status(ship: T5Starship) -> None:
    """Print current freight status."""
    ship_freight = list(ship.get_cargo().get("freight", []))
    for lot in ship_freight:
        print(
            f"\tLot {lot.serial} aboard, {lot.mass} tons, "
            f"lot id: {lot.lot_id}.")
    print(
        f"\tStarship {ship.ship_name} now has {len(ship_freight)} "
        f"freight items on board, with total mass {ship.cargo_size}.")


def _should_depart(ship: T5Starship) -> bool:
    """Check if hold is 80% full; ready to depart."""
    if ship.cargo_size > 0.8 * ship.hold_size:
        print(
            "Met 80% or more criteria for departure at "
            f"{ship.cargo_size / ship.hold_size * 100.0:.1f}%.")
        return True
    return False


def search_and_load_freight(ship: T5Starship, gd: GameDriver) -> None:
    """Search for freight over multiple days until hold is 80% full."""
    searching = True
    sim_day = 0
    while searching:
        print(f"Searching for freight on Day {sim_day}:")
        world = gd.world_data.get(ship.location)
        if not world:
            print(f"\tWorld {ship.location} not found in data.")
            break

        liaison_skill = _get_liaison_skill(ship)
        freight_lot_mass = world.freight_lot_mass(liaison_skill)
        if freight_lot_mass > 0:
            lot = T5Lot(ship.location, gd)
            lot.mass = freight_lot_mass
            print(
                f"\tThe lot size available today is {lot.serial} "
                f"of {lot.mass} tons, lot id: {lot.lot_id}.")
            if not _try_onload_freight_lot(ship, lot):
                searching = False
        else:
            print("\tNo lot available today.")

        _report_hold_status(ship)
        sim_day += 1
        if _should_depart(ship):
            searching = False


def search_and_load_cargo(ship: T5Starship, gd: GameDriver) -> None:
    """Search for cargo to fill remainder of hold from up to 100
    tons of speculative cargo created on the ship's current world."""
    world = gd.world_data.get(ship.location)
    if not world:
        print(f"World {ship.location} not found in data.")
        return

    available_lots = world.generate_speculative_cargo(
        gd,
        max_total_tons=100,
        max_lot_size=ship.hold_size - ship.cargo_size
    )

    print(f"Searching for cargo at {ship.location} to fill hold:")
    for lot in available_lots:
        try:
            ship.onload_lot(lot, "cargo")
            ship.debit(lot.origin_value * lot.mass)
            print(
                f"\tLoaded cargo lot {lot.serial} of {lot.mass} tons, "
                f"lot id: {lot.lot_id}.")
        except ValueError as e:
            print(f"\tCould not load lot {lot.serial} "
                  f"mass {lot.mass}: {e}")

    print(
        f"\tStarship {ship.ship_name} now has "
        f"{len(list(ship.get_cargo()['cargo']))} cargo items on board, "
        f"with total mass {ship.cargo_size}.")


def report_ship_status(ship):
    print(
        f"Starship {ship.ship_name} now has "
        f"balance={ship.balance}, "
        f"cargo_size={ship.cargo_size} with "
        f"{len(list(ship.get_cargo()['cargo']))} cargo items, "
        f"{len(list(ship.get_cargo()['freight']))} freight items, "
        f"({len(list(ship.passengers['high']))} high, "
        f"{len(list(ship.passengers['mid']))} mid, "
        f"{len(list(ship.passengers['low']))} low passengers), and "
        f"{len(ship.get_mail())} mail bundles."
    )


def main() -> None:
    """Run a single starship jump/unload/load cycle."""
    gd = GameDriver()
    origin = "Rhylanor"
    dest = "Jae Tellona"

    # Phase 1: Load ship at origin
    ship = setup_departure(origin, gd)
    report_ship_status(ship)

    # Phase 2: Jump to destination
    ship.set_course_for(dest)
    ship.status = "maneuvering"
    print(f"Starship {ship.ship_name} is maneuvering to {ship.location}"
          f" jump point to {ship.destination()}...")
    ship.status = "traveling"
    print(f"Starship {ship.ship_name} is jumping to "
          f"{ship.destination()} system "
          f"from {ship.location}...")
    ship.location = ship.destination()
    ship.status = "maneuvering"
    print(f"Starship {ship.ship_name} is maneuvering to "
          f"{ship.destination()} starport...")
    ship.status = "docked"
    print(f"Starship {ship.ship_name} arrived at {ship.location} starport; "
          "performing offload and local business")

    # Phase A: Offload passengers and mail
    perform_arrival(ship)

    # Phase B: Sell cargo
    sell_cargo(ship, gd)

    report_ship_status(ship)

    dest = "Rhylanor"
    ship.set_course_for(dest)

    # Phase D: Search for and load freight until 80% full
    print(f"Starship {ship.ship_name} preparing for departure from "
          f"{ship.location} starport bound for {ship.destination()} starport "
          f"and performing local business")
    search_and_load_freight(ship, gd)

    report_ship_status(ship)

    # phase D: Load cargo to fill remaining hold space
    search_and_load_cargo(ship, gd)

    report_ship_status(ship)

    print("End simulation version 0.5")


if __name__ == "__main__":
    main()
