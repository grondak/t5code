import simpy
import csv
import math
from datetime import datetime

# Constants
LOG_FILE = "simulation_log.txt"
SHIP_CLASSES_CSV = "ship_classes.csv"
INPUT_CSV = "ships.csv"
OUTPUT_CSV = "ships_output.csv"
MAP_FILE = "t5_map.txt"

# Load ship classes
def load_ship_classes(file_path):
    ship_classes = {}
    with open(file_path, mode="r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            ship_classes[row["class_name"]] = {
                "jump_rating": int(row["jump_rating"]),
                "maneuver_rating": float(row["maneuver_rating"]),
                "cargo_capacity": int(row["cargo_capacity"]),
            }
    return ship_classes

# Load ships
def load_ships_from_csv(file_path):
    ships = []
    with open(file_path, mode="r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            ships.append({
                "id": row["id"],
                "class_name": row["class_name"],
                "location": row["location"],
                "status": row["status"],
                "fuel": int(row["fuel"]),
                "travel_time": int(row["travel_time"]),
                "departure_time": int(row["departure_time"]),
                "destination": row["destination"],
                "cargo": int(row["cargo"]),
            })
    return ships

# Write output CSV
def save_ships_to_csv(ships, file_path):
    with open(file_path, mode="w", newline="") as csvfile:
        fieldnames = ["id", "class_name", "location", "status", "fuel", "travel_time", "departure_time", "destination", "cargo"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(ships)
        
# Parse T5 map file
def parse_t5_map(file_path):
    systems = {}
    with open(file_path, mode="r") as mapfile:
        reader = csv.DictReader(mapfile, delimiter="\t")
        for row in reader:
            systems[row["Hex"]] = {
                "name": row["Name"],
                "uwp": row["UWP"],
                "zone": row["Zone"],
                "coordinates": (int(row["Hex"][:2]), int(row["Hex"][2:])),  # (X, Y)
            }
    return systems

# Calculate hex distance
def calculate_hex_distance(hex1, hex2):
    x1, y1 = hex1
    x2, y2 = hex2
    return max(abs(x1 - x2), abs(y1 - y2), abs((x1 - y1) - (x2 - y2)))

def get_hex_from_name(system_name, systems):
    """
    Find the hex location of a system given its name.
    
    Args:
        system_name (str): The name of the system (e.g., "Rhylanor").
        systems (dict): The parsed T5 map data.
        
    Returns:
        str: The hex location (e.g., "0312") or None if not found.
    """
    for hex_code, data in systems.items():
        if data["name"].lower() == system_name.lower():  # Case-insensitive match
            return hex_code
    return None

def get_name_from_hex(hex_code, systems):
    """
    Find the system name given its hex location.
    
    Args:
        hex_code (str): The hex location (e.g., "0312").
        systems (dict): The parsed T5 map data.
        
    Returns:
        str: The system name (e.g., "Rhylanor") or None if not found.
    """
    if hex_code in systems:
        return systems[hex_code]["name"]
    return None

# Get valid destinations
def get_valid_destinations(current_system, jump_rating, systems):
    current_hex = get_hex_from_name(current_system, systems)
    valid = []
    print(f"Current hex {current_hex}")
    for hex_code, data in systems.items():
        if data["zone"] in ["A", "R"]:
            continue  # Skip Amber/Red zones
        distance = calculate_hex_distance(
            systems[current_hex]["coordinates"], data["coordinates"]
        )
        if distance <= jump_rating:
            valid.append(get_name_from_hex(hex_code, systems))
    return valid

# Log events
def log_event(message):
    with open(LOG_FILE, mode="a") as logfile:
        logfile.write(f"{datetime.now()}: {message}\n")

# Ship process
def ship_process(env, ship, ship_classes, systems, event_queue):
    while True:
        ship_class = ship_classes[ship["class_name"]]
        current_system = ship["location"]

        log_event(f"Ship {ship['id']} ({ship['class_name']}) is at {current_system} with status {ship['status']} and fuel {ship['fuel']}.")

        if ship["status"] == "traveling":
            # Simulate travel
            yield env.timeout(ship["travel_time"])
            ship["location"] = ship["destination"]
            ship["status"] = "docked"
            log_event(f"Ship {ship['id']} has arrived at {ship['location']} and is now docked.")

        elif ship["status"] == "docked":
            # Choose next destination
            jump_rating = ship_class["jump_rating"]
            valid_destinations = get_valid_destinations(current_system, jump_rating, systems)
            print(valid_destinations, ship["id"])
            if valid_destinations:
                ship["destination"] = valid_destinations[0]  # Example: Choose the first valid destination
                ship["travel_time"] =  168  # Jump travel time (1 week of jumpspace time)

                ship["status"] = "traveling"
                log_event(f"Ship {ship['id']} has departed for {ship['destination']}.")
            else:
                log_event(f"Ship {ship['id']} has no valid destinations and is idle.")
                yield env.timeout(1)
        else:
            log_event(f"Ship {ship['id']} is idle.")
            yield env.timeout(1)

        # Update state for export
        event_queue.append(dict(ship))

# Main simulation
def run_simulation(ship_classes_csv, input_csv, map_file, output_csv, duration=1000):
    env = simpy.Environment()
    ship_classes = load_ship_classes(ship_classes_csv)
    ships = load_ships_from_csv(input_csv)
    systems = parse_t5_map(map_file)
    event_queue = []

    for ship in ships:
        env.process(ship_process(env, ship, ship_classes, systems, event_queue))

    # Run the simulation
    env.run(until=duration)

    # Save final state
    save_ships_to_csv(event_queue, output_csv)

# Run the simulator
run_simulation(SHIP_CLASSES_CSV, INPUT_CSV, MAP_FILE, OUTPUT_CSV)
