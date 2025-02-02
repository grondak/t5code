"""a class that represents the game state and hauls global variables around for all to play with"""
import csv
from T5World import T5World
from T5Lot import *
from T5Starship import *
from T5Mail import *
from T5NPC import *

MAP_FILE = "t5_map.txt"


class GameState:
    worlds = {}
    world_data = None

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
    
if __name__ == '__main__':
    GameState.world_data = T5World.load_all_worlds(GameState.load_and_parse_t5_map(MAP_FILE))
    print(f'Rhylanor is {GameState.world_data['Rhylanor'].UWP()} with Trade Classifications {GameState.world_data['Rhylanor'].trade_classifications()}')
    test_lot = T5Lot('Rhylanor', GameState)
    print(f'The test lot ID is {test_lot.lot_id} with mass {test_lot.mass} and serial {test_lot.serial}')
    print(f'Selling on worlds:')
    for world in ['Porozlo', 'Risek', 'Loneseda', 'Valhalla']:
        print(f'\tWorld: {world} trade classifications: {GameState.world_data[world].trade_classifications()} ' +
              f'tech level: {letter_to_tech_level(GameState.world_data[world].UWP()[8:])} // lot value: {test_lot.determine_sale_value_on(world, GameState)}')
    test_world = 'Efate'
    print(f'{test_world} is {GameState.world_data[test_world].UWP()} with Trade Classifications {GameState.world_data[test_world].trade_classifications()}')
    test_lot = T5Lot(test_world, GameState)
    print(f'The test lot ID is {test_lot.lot_id} with mass {test_lot.mass} and serial {test_lot.serial}')
    print(f'\tSelling World: {world} trade classifications: {GameState.world_data[world].trade_classifications()} ' +
          f'tech level: {letter_to_tech_level(GameState.world_data[world].UWP()[8:])} // lot value: {test_lot.determine_sale_value_on(world, GameState)}')
    npc1 = T5NPC('Admiral Miller')
    npc2 = T5NPC('General Sprange')
    starship = T5Starship('Paprika', 'Rhylanor')
    starship.set_course_for('Jae Tellona')
    mail1 = T5Mail('Rhylanor', 'Jae Tellona', GameState)
    mail2 = T5Mail('Rhylanor', 'Jae Tellona', GameState)
    starship.onload_high_passenger(npc1)
    starship.onload_high_passenger(npc2)
    starship.onload_mail(mail1)
    starship.onload_mail(mail2)
    print(f'\n\n\nStarship {starship.shipName} bound for {starship.destination()}. Contents:')
    for passenger in starship.highPassengers:
        print(f'\tPassenger {passenger.characterName}.')
    for mailItem in starship.get_mail():
        print(f'\tMail bundle with serial number {starship.get_mail()[mailItem].serial}.')
    print(f'Starship {starship.shipName} arriving at {starship.destination()}.')
    starship.location= starship.destination
    starship.set_course_for('Rhylanor')
    print(f'Starship {starship.shipName} now bound for {starship.destination()}.')    
    print('Priority Offload High Passengers!')
    starship.offload_high_passengers()
    print(f'\t{starship.shipName} has {len(starship.highPassengers)} high passengers aboard.')
    print('Priority Offload Mail!')
    starship.offload_mail()
    print(f'\t{starship.shipName} has {len(starship.get_mail())} mail bundles in the mail locker.')
    
    
    print("End simulation version 0.2")