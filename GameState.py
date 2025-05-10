"""a class that represents the game state and hauls global variables around for all to play with"""

import csv
from T5World import T5World
from T5Lot import *
from T5Starship import *
from T5Mail import *
from T5NPC import *

MAP_FILE = "t5_map.txt"
SHIP_CLASSES_FILE = "t5_ship_classes.csv"


class GameState:
    worlds = {}
    world_data = None
    ship_data = None

    # Parse T5 map file
    @staticmethod
    def load_and_parse_t5_map(file_path):
        worlds = {}
        with open(file_path, mode="r") as mapfile:
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

    @staticmethod
    def load_and_parse_t5_ship_classes(file_path):
        ships = {}
        with open(file_path, mode="r") as shipFile:
            reader = csv.DictReader(shipFile)
            for row in reader:
                ships[row["class_name"]] = {
                    "class_name": row["class_name"],
                    "jump_rating": int(row["jump_rating"]),
                    "maneuver_rating": int(row["maneuver_rating"]),
                    "cargo_capacity": float(row["cargo_capacity"]),
                }
        return ships


if __name__ == "__main__":
    GameState.ship_data = T5ShipClass.load_all_ship_classes(
        GameState.load_and_parse_t5_ship_classes(SHIP_CLASSES_FILE)
    )
    GameState.world_data = T5World.load_all_worlds(
        GameState.load_and_parse_t5_map(MAP_FILE)
    )
    print(
        f"Rhylanor is {GameState.world_data['Rhylanor'].UWP()} with Trade Classifications {GameState.world_data['Rhylanor'].trade_classifications()}"
    )
    test_lot = T5Lot("Rhylanor", GameState)
    test_lot.mass = 5
    print(
        f"The test lot ID is {test_lot.lot_id} with mass {test_lot.mass} and serial {test_lot.serial}"
    )
    print(f"Selling on worlds:")
    for world in ["Porozlo", "Risek", "Loneseda", "Valhalla"]:
        print(
            f"\tWorld: {world} trade classifications: {GameState.world_data[world].trade_classifications()} "
            + f"tech level: {letter_to_tech_level(GameState.world_data[world].UWP()[8:])} // lot value: {test_lot.determine_sale_value_on(world, GameState)}"
        )
    print(
        f"\tSelling World: {world} trade classifications: {GameState.world_data[world].trade_classifications()} "
        + f"tech level: {letter_to_tech_level(GameState.world_data[world].UWP()[8:])} // lot value: {test_lot.determine_sale_value_on(world, GameState)}"
    )
    test_world = "Efate"
    print(
        f"{test_world} is {GameState.world_data[test_world].UWP()} with Trade Classifications {GameState.world_data[test_world].trade_classifications()}"
    )
    test_lot2 = T5Lot(test_world, GameState)
    test_lot2.mass = 5
    print(
        f"The test lot ID is {test_lot2.lot_id} with mass {test_lot2.mass} and serial {test_lot2.serial}"
    )
    npc1 = T5NPC("Admiral Miller")
    npc2 = T5NPC("General Sprange")
    npc3 = T5NPC("Colonel Mustard")
    npc4 = T5NPC("Colonel Sanders")
    npc5 = T5NPC("Bones")
    npc5.set_skill("medic", 5)
    starship = T5Starship("Paprika", "Rhylanor", GameState.ship_data["Freighter"])
    starship.set_course_for("Jae Tellona")
    mail1 = T5Mail("Rhylanor", "Jae Tellona", GameState)
    mail2 = T5Mail("Rhylanor", "Jae Tellona", GameState)
    starship.onload_passenger(npc1, "high")
    starship.onload_passenger(npc2, "high")
    starship.onload_passenger(npc3, "mid")
    starship.onload_passenger(npc4, "low")
    starship.hire_crew("medic", npc5)
    starship.onload_lot(test_lot, "freight")
    starship.onload_lot(test_lot2, "freight")
    starship.onload_mail(mail1)
    starship.onload_mail(mail2)
    print(
        f"\n\n\nStarship {starship.shipName} bound for {starship.destination()}. Contents:"
    )
    for passenger in starship.passengers["high"]:
        print(f"\tHigh Passenger {passenger.characterName}.")
    for passenger in starship.passengers["mid"]:
        print(f"\tMid Passenger {passenger.characterName}.")
    for passenger in starship.passengers["low"]:
        print(f"\tLow Passenger {passenger.characterName}.")
    for mailItem in starship.get_mail():
        print(
            f"\tMail bundle with serial number {starship.get_mail()[mailItem].serial}."
        )
    for lot in starship.get_cargo()["freight"]:
        print(f"\tLot {lot.serial} of {lot.mass} tons, lot id: {lot.lot_id}")
    print(
        f"Starship {starship.shipName} has {len(starship.get_cargo()['freight'])} freight items on board"
    )
    print(f"Starship {starship.shipName} arriving at {starship.destination()}.")
    starship.location = starship.destination
    starship.set_course_for("Rhylanor")
    print(f"Starship {starship.shipName} now bound for {starship.destination()}.")
    print("Priority Offload High Passengers!")
    for passenger in starship.offload_passengers("high"):
        print(f"\tOffloaded high passenger {passenger.characterName}")
    print(
        f"\tStarship {starship.shipName} has {len(starship.passengers['high'])} high passengers aboard."
    )
    print("Priority Offload Mail!")
    starship.offload_mail()
    print(
        f"\tStarship {starship.shipName} has {len(starship.get_mail())} mail bundles in the mail locker."
    )
    print("Offload Mid Passengers!")
    for passenger in starship.offload_passengers("mid"):
        print(f"\tOffloaded mid passenger {passenger.characterName}")
    print(
        f"\tStarship {starship.shipName} has {len(starship.passengers['mid'])} mid passengers aboard."
    )
    print("Offload Freight!")
    starshipFreight = list(starship.get_cargo()["freight"])
    for lot in starshipFreight:
        starship.offload_lot(lot.serial, "freight")
        print(f"\tLot {lot.serial} offloaded, {lot.mass} tons, lot id: {lot.lot_id}")
    print(
        f"\tStarship {starship.shipName} has {len(starship.get_cargo()['freight'])} freight items on board"
    )
    print("Offload Low Passengers!")
    for passenger in starship.offload_passengers("low"):
        if passenger.get_state() == "Alive":
            print(f"\tRevived low passenger {passenger.characterName}")
        else:
            print(f"\tThe medic killed low passenger {passenger.characterName}")
    print(
        f"\tStarship {starship.shipName} has {len(starship.passengers['high'])} low passengers aboard."
    )
    print("End simulation version 0.3")
