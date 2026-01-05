"""Game state initialization and data loading utilities.

Provides functions to parse Traveller 5 map and ship class data from CSV files,
which form the foundation for world and ship data in the simulator.
"""

import csv
from typing import Dict, Any, Optional
from .T5Tables import SECTORS


class GameState:
    """Global game state container for world and ship data.

    Provides shared storage for loaded world and ship class data that
    can be accessed across the application. Typically initialized once
    at startup with data from CSV files.

    Attributes:
        worlds: Legacy world storage (deprecated)
        world_data: Dictionary of T5World instances by name
        ship_data: Dictionary of T5ShipClass instances by class name
    """
    worlds: Dict[str, Any] = {}
    world_data: Optional[Dict[str, Any]] = None
    ship_data: Optional[Dict[str, Any]] = None


def load_and_parse_t5_map(file_path: str) -> Dict[str, Dict[str, Any]]:
    """Load and parse Traveller 5 world data from TSV file.

    Args:
        file_path: Path to tab-separated map file

    Returns:
        Dictionary mapping world names to world data dicts with keys:
            - Name: World name
            - UWP: Universal World Profile string
            - Zone: Travel zone (Red/Amber/Green)
            - Coordinates: (x, y) hex tuple
            - TradeClassifications: Space-separated trade codes
            - Importance: Importance rating string

    Example:
        >>> worlds = load_and_parse_t5_map("resources/t5_map.txt")
        >>> print(worlds["Rhylanor"]["UWP"])
        A788899-A
    """
    with open(file_path, mode="r") as mapfile:
        return load_and_parse_t5_map_filelike(mapfile)


def load_and_parse_t5_map_filelike(mapfile) -> Dict[str, Dict[str, Any]]:
    """Load and parse T5 world data from file-like object.

    Args:
        mapfile: File-like object with tab-separated world data

    Returns:
        Dictionary mapping world names to world data dicts
    """
    worlds = {}
    reader = csv.DictReader(mapfile, delimiter="\t")
    for row in reader:
        sector_code = row["SS"]
        sector_name = SECTORS.get(sector_code, sector_code)
        worlds[row["Name"]] = {
            "Name": row["Name"],
            "UWP": row["UWP"],
            "Zone": row["Zone"],
            "Sector": sector_name,
            "Subsector": row["SS"],
            "Hex": row["Hex"],
            "Coordinates": (int(row["Hex"][:2]), int(row["Hex"][2:])),
            "TradeClassifications": row["Remarks"],
            "Importance": row["{Ix}"],
        }
    return worlds


def load_and_parse_t5_ship_classes(
        file_path: str) -> Dict[str, Dict[str, Any]]:
    """Load and parse starship class data from CSV file.

    Args:
        file_path: Path to CSV file with ship class specifications

    Returns:
        Dictionary mapping class names to specification dicts with keys:
            - class_name: Ship class name
            - jump_rating: Jump drive rating
            - maneuver_rating: Maneuver drive rating
            - cargo_capacity: Hold size in tons
            - staterooms: Number of staterooms
            - low_berths: Number of low berth pods

    Example:
        >>> ships = load_and_parse_t5_ship_classes(
                "resources/t5_ship_classes.csv")
        >>> print(ships["Free Trader"]["cargo_capacity"])
        82
    """
    with open(file_path, mode="r") as shipFile:
        return load_and_parse_t5_ship_classes_filelike(shipFile)


def load_and_parse_t5_ship_classes_filelike(
        ship_file) -> Dict[str, Dict[str, Any]]:
    """Load and parse ship class data from file-like object.

    Args:
        ship_file: File-like object with CSV ship class data

    Returns:
        Dictionary mapping class names to specification dicts
    """
    ships = {}
    reader = csv.DictReader(ship_file)
    for row in reader:
        # Parse crew_positions string into list of position codes
        crew_positions_str = row.get("crew_positions", "")
        crew_positions = list(crew_positions_str) if crew_positions_str else []

        ships[row["class_name"]] = {
            "class_name": row["class_name"],
            "jump_rating": int(row["jump_rating"]),
            "maneuver_rating": int(row["maneuver_rating"]),
            "powerplant_rating": int(row.get("powerplant_rating",
                                             row["maneuver_rating"])),
            "cargo_capacity": float(row["cargo_capacity"]),
            "staterooms": int(row["staterooms"]),
            "low_berths": int(row["low_berths"]),
            "crew_positions": crew_positions,
        }
    return ships
