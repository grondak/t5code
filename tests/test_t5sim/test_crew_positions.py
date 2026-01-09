"""Test script for crew positions functionality."""

from t5code.GameState import load_and_parse_t5_ship_classes
from t5code.T5ShipClass import T5ShipClass
from t5code.T5Starship import T5Starship
from t5code.T5Company import T5Company
from t5code.T5NPC import T5NPC

# Load ship classes
ships_data = load_and_parse_t5_ship_classes('resources/t5_ship_classes.csv')
ship_classes = T5ShipClass.load_all_ship_classes(ships_data)

print("=== Ship Class Crew Positions ===")
for class_name, ship_class in ship_classes.items():
    print(f"{class_name}: {ship_class.crew_positions}")

print("\n=== Creating T5Starship instances ===")

# Create a company to own the ships
company = T5Company("Test Company", starting_capital=10_000_000)

# Create a Scout
scout_class = ship_classes['Scout']
scout_ship = T5Starship("Test Scout", "Sol", scout_class, owner=company)
print("\nScout crew_position dictionary:")
for pos_name, positions_list in scout_ship.crew_position.items():
    print(f"  {pos_name}: {len(positions_list)} position(s)")
    for i, crew_pos in enumerate(positions_list):
        print(f"    [{i}] {crew_pos}")

print(f"\nChecking if Captain position [0] is filled: "
      f"{scout_ship.crew_position['Captain'][0].is_filled()}")

# Assign an NPC to the Captain position
# (Captain also serves as pilot on small ships)
captain_npc = T5NPC("Jane 'Ace' Starr")
captain_npc.set_skill("Pilot", 3)
scout_ship.crew_position['Captain'][0].assign(captain_npc)

print("\nAfter assigning captain:")
print(f"  Is filled: {scout_ship.crew_position['Captain'][0].is_filled()}")
print(f"  NPC: {scout_ship.crew_position['Captain'][0].npc.character_name}")
print(f"  Full repr: {scout_ship.crew_position['Captain'][0]}")

# Create a Liner
liner_class = ship_classes['Liner']
liner_ship = T5Starship("Test Liner", "Sol", liner_class, owner=company)
total_positions = (sum(len(positions)
                       for positions in liner_ship.crew_position.values()))
print(f"\nLiner has {total_positions} total positions across "
      f"{len(liner_ship.crew_position)} position types:")
for pos_name, positions_list in liner_ship.crew_position.items():
    count = len(positions_list)
    print(f"  - {pos_name}: {count} position{'s' if count > 1 else ''}")

# Show multiple engineers
print("\nLiner Engineer positions (should be 4):")
for i, eng_pos in enumerate(liner_ship.crew_position['Engineer']):
    print(f"  Engineer {i+1}: {eng_pos}")

# Test the query pattern with list access
print("\n=== Testing query pattern ===")
print(f"scout_ship.crew_position['Captain'][0].is_filled() == "
      f"{scout_ship.crew_position['Captain'][0].is_filled()}")
print(f"scout_ship.crew_position['Engineer'][0].is_filled() == "
      f"{scout_ship.crew_position['Engineer'][0].is_filled()}")
npc_name = (scout_ship.crew_position['Captain'][0].npc.character_name
            if scout_ship.crew_position['Captain'][0].is_filled() else 'None')
print(f"Scout captain NPC: {npc_name}")

# Test checking all positions of a type
print("\n=== Checking all Engineer positions on Liner ===")
for i, eng_pos in enumerate(liner_ship.crew_position['Engineer']):
    filled_status = "filled" if eng_pos.is_filled() else "vacant"
    print(f"  Engineer slot {i}: {filled_status}")
