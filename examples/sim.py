import simpy
import csv
import os
import random

from datetime import datetime, timedelta


# Constants
LOG_FILE = "output/simulation_log.txt"
SHIP_CLASSES_CSV = "resources/t5_ship_classes.csv"
INPUT_CSV = "resources/ships.csv"
OUTPUT_CSV = "output/ships_output.csv"
MAP_FILE = "resources/t5_map.txt"
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
def clock(env, interval=SIM_INTERVAL):
    """
    Simulates a clock that prints the current simulation time.
    """
    while True:
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
            ships.append(
                {
                    "id": row["id"],
                    "class_name": row["class_name"],
                    "location": row["location"],
                    "status": row["status"],
                    "fuel": int(row["fuel"]),
                    "travel_time": int(row["travel_time"]),
                    "departure_time": int(row["departure_time"]),
                    "destination": row["destination"],
                    "cargo": int(row["cargo"]),
                }
            )
    return ships


# Write output CSV
def save_ships_to_csv(ships, file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
    with open(file_path, mode="w", newline="") as csvfile:
        fieldnames = [
            "id",
            "class_name",
            "location",
            "status",
            "fuel",
            "travel_time",
            "departure_time",
            "destination",
            "cargo",
        ]
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
                "coordinates": (int(row["Hex"][:2]), int(row["Hex"][2:])),
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
        if data["name"].lower() == system_name.lower():
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
    for hex_code, data in systems.items():
        if data["zone"] in ["A", "R"]:
            continue  # Skip Amber/Red zones
        if hex_code == current_hex:
            continue  # Don't come back to where we are
        distance = calculate_hex_distance(
            systems[current_hex]["coordinates"], data["coordinates"]
        )
        if distance <= jump_rating:
            valid.append(get_name_from_hex(hex_code, systems))
    return valid


# Log events
def log_event(message, env, start_time):
    with open(LOG_FILE, mode="a") as logfile:
        logfile.write(
            f"{simpy_time_to_timestamp(env, start_time)}: {message}\n")


# Log ship event
def ship_log_event(message, ship, env, start_time):
    log_event(
        f"Ship {ship['id']} ({ship['class_name']} "
        f"{ship['status']} at "
        f"{ship['location']}{" bound for " +
                             ship['destination'] if ship[
                                 'status'] == "traveling"
                             else ""}. Fuel: "
        f" {ship['fuel']} Cargo: "
        f"{ship['cargo']}) {message}",
        env,
        start_time,
    )


# Handle traveling ship
def handle_traveling_ship(env, ship, start_time):
    yield env.timeout(ship["travel_time"])
    ship["location"] = ship["destination"]
    ship["status"] = "docked"
    ship_log_event(
        f"has arrived at {ship['location']} and is now docked.",
        ship,
        env,
        start_time,
    )


# Unload cargo
def unload_cargo(env, ship, start_time):
    unload_divisor = 3
    if ship["cargo"] > 0:
        unloading_time = (ship["cargo"] // unload_divisor) + 1
        yield env.timeout(unloading_time)
        ship["cargo"] = 0
        ship_log_event("has unloaded its cargo.", ship, env, start_time)


# Load cargo
def load_cargo(env, ship, ship_class, start_time):
    load_divisor = 4
    if ship["cargo"] < ship_class["cargo_capacity"]:
        loading_time = (
            (ship_class["cargo_capacity"] - ship["cargo"]) // load_divisor
        ) + 1
        yield env.timeout(loading_time)
        ship["cargo"] = ship_class["cargo_capacity"]
        ship_log_event(
            "has loaded new cargo to full capacity.",
            ship,
            env,
            start_time
        )


# Choose next destination
def choose_next_destination(env,
                            ship,
                            ship_class,
                            current_system,
                            systems,
                            start_time):
    jump_rating = ship_class["jump_rating"]
    valid_destinations = get_valid_destinations(
        current_system, jump_rating, systems
    )
    if valid_destinations:
        ship["destination"] = valid_destinations[0]
        ship["travel_time"] = 168
        ship["status"] = "traveling"
        ship_log_event(
            f"has departed for {ship['destination']}.",
            ship,
            env,
            start_time
        )
    else:
        ship_log_event(
            "has no valid destinations and is idle.",
            ship,
            env,
            start_time
        )
        ship["status"] = "idle"
        yield env.timeout(1)


# Handle docked ship
def handle_docked_ship(env,
                       ship,
                       ship_class,
                       current_system,
                       systems,
                       start_time):
    preunload_business_time = 2
    yield env.timeout(preunload_business_time)
    ship_log_event(
        "has completed ship's business before cargo handling.",
        ship,
        env,
        start_time,
    )

    yield env.process(unload_cargo(env, ship, start_time))
    yield env.process(load_cargo(env, ship, ship_class, start_time))

    post_unload_business_time = 3
    yield env.timeout(post_unload_business_time)
    ship_log_event(
        "has completed ship's business after cargo handling.",
        ship,
        env,
        start_time,
    )

    yield env.process(choose_next_destination(env,
                                              ship,
                                              ship_class,
                                              current_system,
                                              systems,
                                              start_time))


# Handle idle ship
def handle_idle_ship(env, ship, start_time):
    ship_log_event("is idle.", ship, env, start_time)
    might_move = random.randint(1, 10)
    if might_move == 1:
        ship["status"] = "docked"
        ship_log_event("has new orders.", ship, env, start_time)
    yield env.timeout(1)


# Ship process
def ship_process(env, ship, ship_classes, systems, event_queue, start_time):
    while True:
        ship_class = ship_classes[ship["class_name"]]
        current_system = ship["location"]

        ship_log_event(".", ship, env, start_time)

        if ship["status"] == "traveling":
            yield env.process(handle_traveling_ship(env, ship, start_time))
        elif ship["status"] == "docked":
            yield env.process(handle_docked_ship(env,
                                                 ship,
                                                 ship_class,
                                                 current_system,
                                                 systems,
                                                 start_time))
        elif ship["status"] == "idle":
            yield env.process(handle_idle_ship(env, ship, start_time))
        else:
            ship_log_event("is huh.", ship, env, start_time)
            exit(1)

        # Update state for export
        event_queue.append(dict(ship))


# Main simulation
def run_simulation(
    ship_classes_csv,
    input_csv,
    map_file,
    output_csv,
    start_year,
    start_day,
    duration=50,
):  # 5*24*7):
    # Initialize log file
    initialize_log_file(LOG_FILE)
    env = simpy.Environment()
    start_time = initialize_simulation_start(start_year, start_day)
    ship_classes = load_ship_classes(ship_classes_csv)
    ships = load_ships_from_csv(input_csv)
    systems = parse_t5_map(map_file)
    event_queue = []

    log_event("Simulation starting.", env, start_time)
    # Add clock process
    env.process(clock(env, SIM_INTERVAL))

    for ship in ships:
        env.process(
            ship_process(env, ship, ship_classes,
                         systems, event_queue, start_time)
        )

    # Run the simulation
    env.run(until=duration)
    log_event("Simulation complete.", env, start_time)

    # Save final state
    save_ships_to_csv(ships, output_csv)


# Run the simulator
run_simulation(
    SHIP_CLASSES_CSV,
    INPUT_CSV,
    MAP_FILE,
    OUTPUT_CSV,
    START_YEAR,
    START_DAY,
)
