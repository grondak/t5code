"""A class that represents one mail shipment from T5, p220"""

import uuid

from T5Code.GameState import (
    load_and_parse_t5_map,
    load_and_parse_t5_map_filelike,
    load_and_parse_t5_ship_classes,
    load_and_parse_t5_ship_classes_filelike,
)
from T5Code.T5Basics import check_success, letter_to_tech_level, tech_level_to_letter
from T5Code.T5World import T5World


class T5Mail:
    def __init__(self, origin_name, destination_name, GameState):
        if GameState.world_data is None:
            raise ValueError("GameState.world_data has not been initialized!")
        self.origin_name = origin_name
        self.origin_importance = int(
            GameState.world_data[origin_name].importance().strip("{} ").strip("'")
        )
        self.destination_name = destination_name
        self.destination_importance = int(
            GameState.world_data[destination_name].importance().strip("{} ").strip("'")
        )
        if self.origin_importance <= (self.destination_importance + 2):
            raise ValueError(
                "Destination World must be at least Importance-2 less than origin world"
            )
        self.serial = str(uuid.uuid4())
