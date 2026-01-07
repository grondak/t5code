#!/usr/bin/env python3
"""Read and display ship classes from CSV file.

Reads the t5_ship_classes.csv resource file and displays each ship
with all field values labeled by their header names.

Decodes crew position codes to readable position names.

At the end, displays a summary table showing each ship class with its
role, ships, combined frequency, and validation that frequencies sum
to 1.0 per role.

Usage:
    python examples/read_ship_classes.py
"""

import csv
from pathlib import Path
from collections import defaultdict


# Mapping of crew position codes to position names
CREW_POSITION_CODES = {
    '0': 'Captain',
    'A': 'Pilot',
    'B': 'Astrogator',
    'C': 'Engineer',
    'D': 'Medic',
    'E': 'Steward',
    'F': 'Freightmaster',
    'G': 'Sensop',
    'N': 'Cook',
    'T': 'Gunner',
    'Y': 'Able Spacer',
    'Z': 'Spacer',
}


def decode_crew_positions(crew_code: str) -> str:
    """Decode crew position codes to readable position names.

    Args:
        crew_code: String of position codes (e.g., "0AABBCC")

    Returns:
        Comma-separated list of position names,
        with "NO CODE" for unknown codes

    Example:
        decode_crew_positions("0AABBCC") ->
        "Captain, Pilot, Pilot, Astrogator, Astrogator, Engineer, Engineer"
    """
    positions = []
    for code in crew_code:
        if code in CREW_POSITION_CODES:
            positions.append(CREW_POSITION_CODES[code])
        else:
            positions.append(f"NO CODE ({code})")

    return ", ".join(positions)


def main():
    """Read and display ship class data from CSV."""
    # Get the path to the ship classes CSV file
    csv_file = (Path(__file__).parent.parent
                / "resources"
                / "t5_ship_classes.csv")

    if not csv_file.exists():
        print(f"Error: Ship classes file not found at {csv_file}")
        return

    print("=" * 80)
    print("TRAVELLER 5 SHIP CLASSES")
    print("=" * 80)

    # Track ships by role for summary
    ships_by_role = defaultdict(list)

    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)

        # Get field names from header
        if reader.fieldnames is None:
            print("Error: Could not read CSV headers")
            return

        for ship_num, row in enumerate(reader, 1):
            print(f"\nShip #{ship_num}:")
            print("-" * 80)

            for field_name in reader.fieldnames:
                value = row[field_name]

                # Decode crew positions if this is the crew_positions field
                if field_name == "crew_positions":
                    decoded = decode_crew_positions(value)
                    print(f"  {field_name:25s}: {value}")
                    print(f"  {'':<25s}  {decoded}")
                else:
                    print(f"  {field_name:25s}: {value}")

            # Track for summary
            role = row["role"]
            class_name = row["class_name"]
            frequency = float(row["frequency"])
            ships_by_role[role].append((class_name, frequency))

    # Print summary by role
    print("\n" + "=" * 80)
    print("SUMMARY BY ROLE")
    print("=" * 80)

    for role in sorted(ships_by_role.keys()):
        print(f"\n{role.upper()} SHIPS:")
        print("-" * 80)
        ships = ships_by_role[role]
        total_frequency = 0.0

        for class_name, frequency in ships:
            print(f"  {class_name:30s}: {frequency:6.2f}")
            total_frequency += frequency

        # Check if frequencies sum to 1.0
        flag = ""
        if abs(total_frequency - 1.0) > 0.001:
            flag = " ERROR: Does not sum to 1.0!"
        print(f"  {'-' * 30}  {'-' * 6}")
        print(f"  {'TOTAL':30s}: {total_frequency:6.2f}{flag}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
