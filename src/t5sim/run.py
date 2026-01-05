"""Command-line interface for running t5sim simulations.

Usage:
    python -m t5sim.run --ships 50 --days 365
"""

import argparse
import time
from t5sim.simulation import run_simulation


def main():
    """Parse arguments and run simulation."""
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

    args = parser.parse_args()

    print("=" * 70)
    print("T5SIM - Traveller 5 Trading Simulation")
    print("=" * 70)
    print(f"Ships: {args.ships}")
    print(f"Duration: {args.days} days")
    print()

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


if __name__ == "__main__":
    main()
