"""a class that represents the game state and hauls global variables around for all to play with"""
import csv
from T5World import T5World
from T5Lot import *

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
              'tech level: {letter_to_tech_level(GameState.world_data[world].UWP()[8:])} // lot value: {test_lot.determine_sale_value_on(world, GameState)}')
    test_world = 'Efate'
    print(f'{test_world} is {GameState.world_data[test_world].UWP()} with Trade Classifications {GameState.world_data[test_world].trade_classifications()}')
    test_lot = T5Lot(test_world, GameState)
    print(f'The test lot ID is {test_lot.lot_id} with mass {test_lot.mass} and serial {test_lot.serial}')
    print(f'\tSelling World: {world} trade classifications: {GameState.world_data[world].trade_classifications()} ' +
          'tech level: {letter_to_tech_level(GameState.world_data[world].UWP()[8:])} // lot value: {test_lot.determine_sale_value_on(world, GameState)}')
        