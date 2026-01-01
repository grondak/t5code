"""Game state initialization and data loading utilities.

Provides functions to parse Traveller 5 map and ship class data from CSV files,
which form the foundation for world and ship data in the simulator.
"""

import csv
from typing import Dict, Any, Optional


class GameState:
    worlds: Dict[str, Any] = {}
    world_data: Optional[Dict[str, Any]] = None
    ship_data: Optional[Dict[str, Any]] = None

    # Parse T5 map file


def load_and_parse_t5_map(file_path):
    with open(file_path, mode="r") as mapfile:
        return load_and_parse_t5_map_filelike(mapfile)


def load_and_parse_t5_map_filelike(mapfile):
    worlds = {}
    reader = csv.DictReader(mapfile, delimiter="\t")
    for row in reader:
        worlds[row["Name"]] = {
            "Name": row["Name"],
            "UWP": row["UWP"],
            "Zone": row["Zone"],
            "Coordinates": (int(row["Hex"][:2]), int(row["Hex"][2:])),
            "TradeClassifications": row["Remarks"],
            "Importance": row["{Ix}"],
        }
    return worlds


def load_and_parse_t5_ship_classes(file_path):
    with open(file_path, mode="r") as shipFile:
        return load_and_parse_t5_ship_classes_filelike(shipFile)


def load_and_parse_t5_ship_classes_filelike(ship_file):
    ships = {}
    reader = csv.DictReader(ship_file)
    for row in reader:
        ships[row["class_name"]] = {
            "class_name": row["class_name"],
            "jump_rating": int(row["jump_rating"]),
            "maneuver_rating": int(row["maneuver_rating"]),
            "cargo_capacity": float(row["cargo_capacity"]),
            "staterooms": int(row["staterooms"]),
            "low_berths": int(row["low_berths"]),
        }
    return ships
