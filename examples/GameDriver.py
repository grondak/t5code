"""a class that represents the game state and hauls global variables around for all to play with"""

import csv
from T5Code import (
    T5Lot,
    T5Mail,
    T5NPC,
    T5ShipClass,
    T5Starship,
    T5World,
    letter_to_tech_level,
    find_best_broker,
    GameState,
)

# import T5Code

MAP_FILE = "t5_map.txt"
SHIP_CLASSES_FILE = "t5_ship_classes.csv"


class GameDriver:
    world_data = None
    ship_data = None


if __name__ == "__main__":
    GameDriver.ship_data = T5ShipClass.load_all_ship_classes(
        GameState.load_and_parse_t5_ship_classes(SHIP_CLASSES_FILE)
    )
    GameDriver.world_data = T5World.load_all_worlds(
        GameState.load_and_parse_t5_map(MAP_FILE)
    )
    print(
        f"Rhylanor is {GameDriver.world_data['Rhylanor'].UWP()} with Trade Classifications {GameDriver.world_data['Rhylanor'].trade_classifications()}."
    )
    test_lot1 = T5Lot("Rhylanor", GameDriver)
    test_lot1.mass = 5
    print(
        f"The test lot ID is {test_lot1.lot_id} with mass {test_lot1.mass} and serial {test_lot1.serial}."
    )
    print(f"Selling on worlds:")
    for world in ["Porozlo", "Risek", "Loneseda", "Valhalla"]:
        print(
            f"\tWorld: {world} trade classifications: {GameDriver.world_data[world].trade_classifications()} "
            + f"tech level: {letter_to_tech_level(GameDriver.world_data[world].UWP()[8:])} // lot value: {test_lot1.determine_sale_value_on(world, GameDriver)}."
        )
    print(
        f"\tSelling World: {world} trade classifications: {GameDriver.world_data[world].trade_classifications()} "
        + f"tech level: {letter_to_tech_level(GameDriver.world_data[world].UWP()[8:])} // lot value: {test_lot1.determine_sale_value_on(world, GameDriver)}."
    )
    test_world = "Efate"
    print(
        f"{test_world} is {GameDriver.world_data[test_world].UWP()} with Trade Classifications {GameDriver.world_data[test_world].trade_classifications()}."
    )
    test_lot2 = T5Lot(test_world, GameDriver)
    test_lot2.mass = 5
    print(
        f"The test lot ID is {test_lot2.lot_id} with mass {test_lot2.mass} and serial {test_lot2.serial}."
    )
    test_lot3 = T5Lot(test_world, GameDriver)
    test_lot3.mass = 5
    print(
        f"The test lot ID is {test_lot3.lot_id} with mass {test_lot3.mass} and serial {test_lot3.serial}."
    )
    npc1 = T5NPC("Admiral Miller")
    npc2 = T5NPC("General Sprange")
    npc3 = T5NPC("Colonel Mustard")
    npc4 = T5NPC("Colonel Sanders")
    npc5 = T5NPC("Bones")
    npc5.set_skill("medic", 5)
    starship = T5Starship("Paprika", "Rhylanor", GameDriver.ship_data["Freighter"])
    starship.set_course_for("Jae Tellona")
    mail1 = T5Mail("Rhylanor", "Jae Tellona", GameDriver)
    starship.onload_passenger(npc1, "high")
    starship.onload_passenger(npc2, "high")
    starship.onload_passenger(npc3, "mid")
    starship.onload_passenger(npc4, "low")
    starship.hire_crew("medic", npc5)
    starship.onload_lot(test_lot1, "freight")
    starship.onload_lot(test_lot2, "freight")
    starship.onload_lot(test_lot3, "cargo")
    starship.onload_mail(mail1)
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
    if len(starship.get_cargo()["freight"]) > 0:
        print(
            f"\tThere are {len(starship.get_cargo()['freight'])} freight items aboard:"
        )
        for lot in starship.get_cargo()["freight"]:
            print(
                f"\t\tFreight Lot {lot.serial} of {lot.mass} tons, lot id: {lot.lot_id}"
            )

    if len(starship.get_cargo()["cargo"]) > 0:
        print(f"\tThere are {len(starship.get_cargo()['cargo'])} cargo items aboard:")
        for lot in starship.get_cargo()["cargo"]:
            print(
                f"\t\tCargo Lot {lot.serial} of {lot.mass} tons, lot id: {lot.lot_id}"
            )

    print(
        f"\n\n\nStarship {starship.shipName} JUMPING to {starship.destination()}\n\n\n"
    )
    print(f"Starship {starship.shipName} arriving at {starship.destination()}.")
    starship.location = starship.destination()
    starship.set_course_for("Rhylanor")
    print(f"Starship {starship.shipName} now bound for {starship.destination()}.")
    print("Priority Offload High Passengers!")
    for passenger in starship.offload_passengers("high"):
        print(f"\tOffloaded high passenger {passenger.characterName}.")
    print(
        f"\tStarship {starship.shipName} now has {len(starship.passengers['high'])} high passengers aboard."
    )
    print("Priority Offload Mail!")
    starship.offload_mail()
    print(
        f"\tStarship {starship.shipName} now has {len(starship.get_mail())} mail bundles in the mail locker."
    )
    print("Offload Mid Passengers!")
    for passenger in starship.offload_passengers("mid"):
        print(f"\tOffloaded mid passenger {passenger.characterName}.")
    print(
        f"\tStarship {starship.shipName} now has {len(starship.passengers['mid'])} mid passengers aboard."
    )
    print("Offload Freight!")
    starshipFreight = list(starship.get_cargo()["freight"])
    for lot in starshipFreight:
        starship.offload_lot(lot.serial, "freight")
        print(f"\tLot {lot.serial} offloaded, {lot.mass} tons, lot id: {lot.lot_id}.")
    print(
        f"\tStarship {starship.shipName} now has {len(starship.get_cargo()['freight'])} freight items on board."
    )
    print("Awakening Low Passengers!")
    for passenger in starship.offload_passengers("low"):
        if passenger.get_state() == "Alive":
            print(f"\tAwakened low passenger {passenger.characterName}.")
        else:
            print(f"\tThe medic killed low passenger {passenger.characterName}.")
    print(
        f"\tStarship {starship.shipName} now has {len(starship.passengers['high'])} low passengers aboard."
    )
    starport = GameDriver.world_data[starship.location].get_starport()
    print(f"The starport on {starship.location} is type {starport}.")
    best_broker = find_best_broker(starport)
    print(f"The best broker on this world is {best_broker}")
    print("Selling Cargo!")
    starshipCargo = list(starship.get_cargo()["cargo"])

    for lot in starshipCargo:
        localCargoMarketPrice = lot.determine_sale_value_on(
            starship.location, GameDriver
        )
        print(
            f"\tSelling cargo lot id: {lot.serial} on {starship.location} for Cr{localCargoMarketPrice}."
        )
        value_modifier = lot.consult_actual_value_table(best_broker["mod"])
        actual_value = localCargoMarketPrice * value_modifier
        print(
            f"\t\tPost-broker Actual Value of cargo lot id {lot.lot_id} is Cr{actual_value}."
        )
        broker_fee = actual_value * best_broker["rate"]
        final_value = actual_value - broker_fee
        starship.credit(final_value)
        print(
            f"\t\tCrediting Cr{final_value} after subtracting broker fee of Cr{broker_fee}."
        )
        starship.offload_lot(lot.serial, "cargo")

    print(
        f"\tStarship {starship.shipName} now has {len(list(starship.get_cargo()["cargo"]))} cargo items on board."
    )
    print(f"Starship {starship.shipName}'s bank account now has Cr{starship.balance}.")
    searching = True
    simDay = 0
    while searching:
        print(f"Searching for Freight/Cargo/Mail on Day {simDay}:")
        freightLotMass = GameDriver.world_data[starship.location].freight_lot_mass(
            starship.bestCrewSkill["Liaison"]
        )
        if freightLotMass > 0:
            lot = T5Lot(starship.location, GameDriver)
            lot.mass = freightLotMass
            print(
                f"\tThe lot size available today is {lot.serial} of {lot.mass} tons, lot id: {lot.lot_id}."
            )
            try:
                starship.onload_lot(lot, "freight")
                starship.credit(1000 * lot.mass)
            except ValueError as e:
                if "Lot will not fit" in str(e):
                    searching = False
                    print(f"Rejecting lot because {lot.mass} is too big for the ship.")
                else:
                    raise
        else:
            print("\tNo lot available today.")
        starshipFreight = list(starship.get_cargo()["freight"])
        for lot in starshipFreight:
            print(f"\tLot {lot.serial} aboard, {lot.mass} tons, lot id: {lot.lot_id}.")
        print(
            f"\tStarship {starship.shipName} now has {len(starship.get_cargo()['freight'])} freight items on board, with total mass {starship.cargoSize}."
        )
        simDay += 1
        if starship.cargoSize > 0.8 * starship.holdSize:
            searching = False
            print(
                f"Met 80% or more criteria for departure at {starship.cargoSize/starship.holdSize*100.0}%."
            )
    print(f"Starship {starship.shipName}'s bank account now has Cr{starship.balance}.")
    print("End simulation version 0.3")
