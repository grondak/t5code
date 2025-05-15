"""a class that represents the game state and hauls global variables around for all to play with"""

import csv


class GameState:
    worlds = {}
    world_data = None
    ship_data = None

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
            "Coordinates": (int(row["Hex"][:2]), int(row["Hex"][2:])),  # (X, Y)
            "TradeClassifications": row["Remarks"],
            "Importance": row["{Ix}"],
        }
    return worlds


def load_and_parse_t5_ship_classes(file_path):
    with open(file_path, mode="r") as shipFile:
        return load_and_parse_t5_ship_classes_filelike(shipFile)


def load_and_parse_t5_ship_classes_filelike(shipFile):
    ships = {}
    reader = csv.DictReader(shipFile)
    for row in reader:
        ships[row["class_name"]] = {
            "class_name": row["class_name"],
            "jump_rating": int(row["jump_rating"]),
            "maneuver_rating": int(row["maneuver_rating"]),
            "cargo_capacity": float(row["cargo_capacity"]),
        }
    return ships
