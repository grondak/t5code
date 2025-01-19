import simpy
import csv
import math
import os
from datetime import datetime, timedelta


# Constants
LOG_FILE = "simulation_log.txt"
SHIP_CLASSES_CSV = "ship_classes.csv"
INPUT_CSV = "ships.csv"
OUTPUT_CSV = "ships_output.csv"
MAP_FILE = "t5_map.txt"
START_YEAR = 1107
START_DAY = 1
SIM_INTERVAL = 1  # 1 hour in simulation time


# Function to remove the log file if it exists
def initialize_log_file(log_file):
    """
    Removes the log file if it exists to ensure a fresh start.
    """
    if os.path.exists(log_file):
        os.remove(log_file)


# Helper: Initialize start time
def initialize_simulation_start(year, day):
    """
    Returns the datetime object representing the start of the simulation.
    """
    base_date = datetime(year=year, month=1, day=1)  # Yearly start
    sim_start = base_date + timedelta(days=day - 1)
    return sim_start

# Helper: Convert SimPy time to timestamp
def simpy_time_to_timestamp(env, start_time):
    """
    Converts SimPy's current time (in hours) to a human-readable timestamp.
    """
    elapsed_time = timedelta(hours=env.now)
    current_time = start_time + elapsed_time
    return current_time.strftime("%Y-%j %H:%M")  # Year-Day Hour:Minute

# Process: Custom clock
def clock(env, start_time, interval=SIM_INTERVAL):
    """
    Simulates a clock that prints the current simulation time.
    """
    while True:
        timestamp = simpy_time_to_timestamp(env, start_time)
        print(f"Simulation Time: {timestamp}")
        yield env.timeout(interval)



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
        if hex_code == current_hex:
            continue # Don't come back to where we are
        distance = calculate_hex_distance(
            systems[current_hex]["coordinates"], data["coordinates"]
        )
        if distance <= jump_rating:
            valid.append(get_name_from_hex(hex_code, systems))
    return valid

# Log events
def log_event(message, env, start_time):
    with open(LOG_FILE, mode="a") as logfile:
        logfile.write(f"{simpy_time_to_timestamp(env, start_time)}: {message}\n")

# Ship process
def ship_process(env, ship, ship_classes, systems, event_queue, start_time):
    while True:
        ship_class = ship_classes[ship["class_name"]]
        current_system = ship["location"]

        log_event(f"Ship {ship['id']} ({ship['class_name']}) is at {current_system} with status {ship['status']} and fuel {ship['fuel']}.", env, start_time)

        if ship["status"] == "traveling":
            # Simulate travel
            yield env.timeout(ship["travel_time"])
            ship["location"] = ship["destination"]
            ship["status"] = "docked"
            log_event(f"Ship {ship['id']} has arrived at {ship['location']} and is now docked.", env, start_time)

        elif ship["status"] == "docked":
            # Choose next destination
            jump_rating = ship_class["jump_rating"]
            valid_destinations = get_valid_destinations(current_system, jump_rating, systems)
            print(valid_destinations, ship["id"])
            if valid_destinations:
                ship["destination"] = valid_destinations[0]  # Example: Choose the first valid destination
                ship["travel_time"] =  168  # Jump travel time (1 week of jumpspace time)

                ship["status"] = "traveling"
                log_event(f"Ship {ship['id']} has departed for {ship['destination']}.", env, start_time)
            else:
                log_event(f"Ship {ship['id']} has no valid destinations and is idle.", env, start_time)
                yield env.timeout(1)
        else:
            log_event(f"Ship {ship['id']} is idle.", env, start_time)
            yield env.timeout(1)

        # Update state for export
        event_queue.append(dict(ship))

# Main simulation
def run_simulation(ship_classes_csv, input_csv, map_file, output_csv, start_year, start_day, duration=4*24*7):
    # Initialize log file
    initialize_log_file(LOG_FILE)
    env = simpy.Environment()
    start_time = initialize_simulation_start(start_year, start_day)
    ship_classes = load_ship_classes(ship_classes_csv)
    ships = load_ships_from_csv(input_csv)
    systems = parse_t5_map(map_file)
    event_queue = []

    # Add clock process
    env.process(clock(env, start_time, SIM_INTERVAL))

    for ship in ships:
        env.process(ship_process(env, ship, ship_classes, systems, event_queue, start_time))

    # Run the simulation
    env.run(until=duration)

    # Save final state
    save_ships_to_csv(event_queue, output_csv)

# Run the simulator
run_simulation(SHIP_CLASSES_CSV, INPUT_CSV, MAP_FILE, OUTPUT_CSV, START_YEAR, START_DAY, )
