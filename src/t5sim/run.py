"""Command-line interface for running t5sim simulations.

Provides argparse-based CLI for executing simulations with
customizable parameters. Handles argument parsing, progress
reporting, and formatted results output.

Usage:
    python -m t5sim.run --ships 50 --days 365 --verbose
    python -m t5sim.run --ships 10 --days 100 --year 1105
    python -m t5sim.run --ships 2 --days 45 --ledger Trader_001
    python -m t5sim.run --ships 2 --days 45 --ledger-all

Arguments:
    --ships: Number of merchant starships to simulate
    --days: Simulation duration in days (can be fractional)
    --map: Path to world data file
    --ships-file: Path to ship classes CSV
    --verbose: Print detailed status updates during simulation
    --year: Starting year in Traveller calendar
    --day: Starting day of year (1-365)
    --ledger: Print ledger for specific ship (e.g., Trader_001)
    --ledger-all: Print ledgers for all ships (verbose)

Output:
    Prints summary with total voyages, cargo sales, profit,
    timing information, averages per ship, and top/bottom 5
    ships by balance.
"""

import argparse
import time
from t5sim.simulation import Simulation
from t5code.GameState import GameState
from t5code import T5World
from t5code import GameState as gs_module


def _create_argument_parser():
    """Create and configure the argument parser.

    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description="Run Traveller 5 trade simulation"
    )
    parser.add_argument(
        "--ships",
        type=int,
        default=10,
        help="Number of starships to simulate (default: 10)",
    )
    parser.add_argument(
        "--days",
        type=float,
        default=365.0,
        help="Simulation duration in days (default: 365)",
    )
    parser.add_argument(
        "--map",
        type=str,
        default="resources/t5_map.txt",
        help="Path to world data file",
    )
    parser.add_argument(
        "--ships-file",
        type=str,
        default="resources/t5_ship_classes.csv",
        help="Path to ship classes file",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print detailed status updates during simulation",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=1104,
        help="Starting year in Traveller calendar (default: 1104)",
    )
    parser.add_argument(
        "--day",
        type=int,
        default=360,
        help="Starting day of year, 1-365 (default: 360)",
    )
    parser.add_argument(
        "--ledger",
        type=str,
        default=None,
        help="Print ledger for specific ship (e.g., Trader_001)",
    )
    parser.add_argument(
        "--ledger-all",
        action="store_true",
        help="Print ledgers for all ships (verbose)",
    )
    parser.add_argument(
        "--include-civilian",
        action="store_true",
        help="Include civilian ships (Scout, Free Trader, etc.)",
    )
    parser.add_argument(
        "--include-military",
        action="store_true",
        help="Include military ships (Close Escort, Corsair, etc.)",
    )
    parser.add_argument(
        "--include-specialized",
        action="store_true",
        help="Include specialized ships (Safari Ship, Packet, Lab Ship)",
    )
    parser.add_argument(
        "--worlds-report",
        action="store_true",
        help="Print detailed report of all worlds and ship locations "
             "at end of simulation",
    )
    return parser


def _filter_ships_by_role(raw_ships, include_civilian, include_military,
                          include_specialized):
    """Filter ship classes based on role selection.

    Args:
        raw_ships: Dictionary of all ship classes
        include_civilian: Include civilian ships
        include_military: Include military ships
        include_specialized: Include specialized ships

    Returns:
        Dictionary of filtered ship classes

    Raises:
        ValueError: If a requested role has no ships available
    """
    # If no roles specified, include all ships
    if not (include_civilian or include_military or include_specialized):
        return raw_ships

    # Build list of requested roles
    requested_roles = []
    if include_civilian:
        requested_roles.append("civilian")
    if include_military:
        requested_roles.append("military")
    if include_specialized:
        requested_roles.append("specialized")

    # Check that each requested role has ships
    available_roles = {ship["role"] for ship in raw_ships.values()}
    for role in requested_roles:
        if role not in available_roles:
            raise ValueError(
                f"No ships with role '{role}' found in ship classes file"
            )

    # Filter ships by requested roles
    filtered = {
        name: ship_data
        for name, ship_data in raw_ships.items()
        if ship_data["role"] in requested_roles
    }

    if not filtered:
        raise ValueError(
            "No ships match the selected roles"
        )  # pragma: no cover (defensive)

    return filtered


def _validate_role_frequencies(raw_ships: dict[str, dict]) -> None:
    """Validate that frequencies per role sum to 1.0.

    Groups all ship classes by their `role` and sums the `frequency` field
    for each role. If any role's total differs from 1.0 beyond a small
    tolerance, raises ValueError describing the problematic roles.

    Args:
        raw_ships: Mapping of class name -> ship data dict, each containing
                   at least `role` (str) and `frequency` (float-like)

    Raises:
        ValueError: If any role's total frequency != 1.0 within tolerance.
    """
    from collections import defaultdict

    totals: dict[str, float] = defaultdict(float)
    for ship in raw_ships.values():
        role = ship.get("role", "civilian")
        try:
            freq = float(ship.get("frequency", 0.0))
        except (TypeError, ValueError):
            freq = 0.0
        totals[role] += freq

    # Allow small floating point tolerance
    TOL = 1e-6
    bad = [(role, total) for role, total in totals.items()
           if abs(total - 1.0) > TOL]

    if bad:
        parts = [f"role '{role}' sums to {total:.2f} (expected 1.00)"
                 for role, total in sorted(bad)]
        msg = "Frequency totals invalid: " + "; ".join(parts)
        raise ValueError(msg)


def _print_ship_list(ships, count, label, sim):
    """Print formatted list of ships with their details.

    Args:
        ships: List of ships to display
        count: Number of ships to show
        label: Label for the list (e.g., "Top 3 ships")
        sim: Simulation object (or None) for world name lookup
    """
    print(f"\n{label}")
    for i, ship in enumerate(ships[:count], 1):
        # Get location display with world name if available
        location = ship.get('location', 'Unknown')
        if sim:
            world = sim.game_state.world_data.get(location)
            location_display = world.full_name() if world else location
        else:
            location_display = location

        ship_class = ship.get('ship_class', 'Unknown')
        print(
            f"  {i}. {ship['name']}, a {ship_class} @ {location_display}: "
            f"Cr{ship['balance']:,.2f} ({ship['voyages']} voyages)"
        )


def _run_with_full_simulation(args):
    """Run simulation with full Simulation object for ledger printing.

    Args:
        args: Parsed command-line arguments

    Returns:
        Tuple of (results dict, simulation object, elapsed time)
    """
    # Initialize game state
    game_state = GameState()
    raw_worlds = gs_module.load_and_parse_t5_map(args.map)
    raw_ships = gs_module.load_and_parse_t5_ship_classes(args.ships_file)
    # Validate role frequencies across the entire file
    _validate_role_frequencies(raw_ships)

    # Filter ships by role if requested
    filtered_ships = _filter_ships_by_role(
        raw_ships,
        args.include_civilian,
        args.include_military,
        args.include_specialized
    )

    # Convert worlds to T5World objects
    game_state.world_data = T5World.load_all_worlds(raw_worlds)
    game_state.ship_classes = filtered_ships

    # Create and run simulation
    start_time = time.time()
    sim = Simulation(
        game_state,
        num_ships=args.ships,
        duration_days=args.days,
        verbose=args.verbose,
        starting_year=args.year,
        starting_day=args.day,
        include_civilian=args.include_civilian,
        include_military=args.include_military,
        include_specialized=args.include_specialized,
    )
    results = sim.run()
    elapsed_time = time.time() - start_time

    return results, sim, elapsed_time


def _run_with_convenience_function(args):
    """Run simulation using convenience function.

    Args:
        args: Parsed command-line arguments

    Returns:
        Tuple of (results dict, None, elapsed time)
    """
    # Initialize game state
    game_state = GameState()
    raw_worlds = gs_module.load_and_parse_t5_map(args.map)
    raw_ships = gs_module.load_and_parse_t5_ship_classes(args.ships_file)
    # Validate role frequencies across the entire file
    _validate_role_frequencies(raw_ships)

    # Filter ships by role if requested
    filtered_ships = _filter_ships_by_role(
        raw_ships,
        args.include_civilian,
        args.include_military,
        args.include_specialized
    )

    # Convert worlds to T5World objects
    game_state.world_data = T5World.load_all_worlds(raw_worlds)
    game_state.ship_classes = filtered_ships

    # Create and run simulation
    start_time = time.time()
    sim = Simulation(
        game_state,
        num_ships=args.ships,
        duration_days=args.days,
        verbose=args.verbose,
        starting_year=args.year,
        starting_day=args.day,
        include_civilian=args.include_civilian,
        include_military=args.include_military,
        include_specialized=args.include_specialized,
    )
    results = sim.run()
    elapsed_time = time.time() - start_time

    return results, None, elapsed_time


def _print_ship_leaderboards(results, sim):
    """Print top/bottom/broke ship leaderboards.

    Only includes civilian ships in the top/bottom rankings.
    Military and specialized ships are excluded from leaderboards.
    If no civilian ships exist, the top/bottom leaderboards are not printed
    but broke ships are still displayed.

    Args:
        results: Simulation results dictionary with ship data
        sim: Simulation object (or None) for world name lookup
    """
    # Separate broke ships from active ships
    all_ships = results["ships"]
    broke_ships = [s for s in all_ships if s.get("broke", False)]
    active_ships = [s for s in all_ships if not s.get("broke", False)]

    # Filter active ships to only civilian ships for leaderboard
    civilian_active_ships = [s for s in active_ships
                             if s.get("role", "civilian") == "civilian"]

    # Sort civilian ships by balance if any exist
    if civilian_active_ships:
        sorted_active = sorted(civilian_active_ships,
                               key=lambda s: s["balance"],
                               reverse=True)

        # Determine how many ships to show
        # (max 5, or fewer if less than 5 total)
        num_active = len(sorted_active)
        top_count = min(5, num_active)
        bottom_count = min(5, num_active)

        # Handle singular vs plural
        if top_count == 1:
            top_label = "Top ship by balance:"
        else:
            top_label = f"Top {top_count} ships by balance:"

        if bottom_count == 1:
            bottom_label = "Bottom ship by balance:"
        else:
            bottom_label = f"Bottom {bottom_count} ships by balance:"

        # Print top ships
        _print_ship_list(sorted_active, top_count, top_label, sim)
        _print_ship_list(sorted_active[-bottom_count:], bottom_count,
                         bottom_label, sim)

    # Print broke ships if any (include military/specialized broke ships)
    if broke_ships:
        sorted_broke = sorted(broke_ships, key=lambda s: s["balance"],
                              reverse=True)
        broke_count = len(broke_ships)

        if broke_count == 1:
            broke_label = "Broke ship:"
        else:
            broke_label = f"Broke ships ({broke_count}):"

        _print_ship_list(sorted_broke, broke_count, broke_label, sim)


def main():
    """Parse arguments and run simulation.

    Entry point for CLI execution. Parses command-line arguments,
    prints configuration summary, executes simulation via
    run_simulation(), measures execution time, and displays
    formatted results.

    Outputs:
        - Configuration summary (ships, duration)
        - Progress messages during execution
        - Results summary (voyages, sales, profit)
        - Performance timing
        - Per-ship averages
        - Top 5 and bottom 5 ships by balance

    Exit Behavior:
        Completes normally on success. Exceptions from simulation
        propagate to caller (not caught here).
    """
    parser = _create_argument_parser()
    args = parser.parse_args()

    print("=" * 70)
    print("T5SIM - Traveller 5 Trading Simulation")
    print("=" * 70)
    print(f"Ships: {args.ships}")
    print(f"Duration: {args.days} days")
    print()

    # Choose execution path based on ledger or worlds report requirements
    if args.ledger or args.ledger_all or args.worlds_report:
        results, sim, elapsed_time = _run_with_full_simulation(args)
    else:
        results, sim, elapsed_time = _run_with_convenience_function(args)

    print("\n" + "=" * 70)
    print("SIMULATION RESULTS")
    print("=" * 70)
    print(f"Total voyages completed: {results['total_voyages']}")
    print(f"Total cargo sales: {results['cargo_sales']}")
    print(f"Total profit: Cr{results['total_profit']:,.2f}")

    # Build timing message with parameters
    timing_msg = (f"Simulation time: {elapsed_time:.2f} seconds "
                  f"({args.ships} ships, {args.days} days)")
    print(timing_msg)

    print("\nAverage per ship:")
    print(f"  Voyages: {results['total_voyages'] / results['num_ships']:.1f}")
    print(
        f"  Profit: Cr{results['total_profit'] / results['num_ships']:,.2f}"
    )

    # Print ship leaderboards
    _print_ship_leaderboards(results, sim)

    # Print ledgers if requested
    if sim:
        if args.ledger_all:
            sim.print_all_ledgers()
        elif args.ledger:
            try:
                sim.print_ledger(args.ledger)
            except ValueError as e:
                print(f"\nError: {e}")

        # Print worlds report if requested
        if args.worlds_report:
            sim.print_worlds_report()


if __name__ == "__main__":  # pragma: no cover
    main()  # pragma: no cover
