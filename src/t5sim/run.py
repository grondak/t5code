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
from t5sim.simulation import run_simulation, Simulation
from t5code.GameState import GameState
from t5code import T5World
from t5code import GameState as gs_module


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

    args = parser.parse_args()

    print("=" * 70)
    print("T5SIM - Traveller 5 Trading Simulation")
    print("=" * 70)
    print(f"Ships: {args.ships}")
    print(f"Duration: {args.days} days")
    print()

    # If ledger printing requested, need full Simulation object
    if args.ledger or args.ledger_all:
        # Initialize game state
        game_state = GameState()
        raw_worlds = gs_module.load_and_parse_t5_map(args.map)
        raw_ships = gs_module.load_and_parse_t5_ship_classes(
            args.ships_file
        )

        # Convert worlds to T5World objects
        game_state.world_data = T5World.load_all_worlds(raw_worlds)
        game_state.ship_classes = raw_ships

        # Create and run simulation
        start_time = time.time()
        sim = Simulation(
            game_state,
            num_ships=args.ships,
            duration_days=args.days,
            verbose=args.verbose,
            starting_year=args.year,
            starting_day=args.day,
        )
        results = sim.run()
        elapsed_time = time.time() - start_time
    else:
        # Use convenience function
        start_time = time.time()
        results = run_simulation(
            map_file=args.map,
            ship_classes_file=args.ships_file,
            num_ships=args.ships,
            duration_days=args.days,
            verbose=args.verbose,
            starting_year=args.year,
            starting_day=args.day,
        )
        elapsed_time = time.time() - start_time
        sim = None

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

    print("\nTop 5 ships by balance:")
    sorted_ships = sorted(
        results["ships"], key=lambda s: s["balance"], reverse=True
    )
    for i, ship in enumerate(sorted_ships[:5], 1):
        print(
            f"  {i}. {ship['name']}: Cr{ship['balance']:,.2f} "
            f"({ship['voyages']} voyages)"
        )

    print("\nBottom 5 ships by balance:")
    for i, ship in enumerate(sorted_ships[-5:], 1):
        print(
            f"  {i}. {ship['name']}: Cr{ship['balance']:,.2f} "
            f"({ship['voyages']} voyages)"
        )

    # Print ledgers if requested
    if sim:
        if args.ledger_all:
            sim.print_all_ledgers()
        elif args.ledger:
            try:
                sim.print_ledger(args.ledger)
            except ValueError as e:
                print(f"\nError: {e}")


if __name__ == "__main__":
    main()
