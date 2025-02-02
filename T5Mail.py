"""A class that represents one mail shipment from T5, p220"""
from T5Basics import *
from GameState import *
from T5World import *
import uuid

class T5Mail:
    def __init__(self, origin_name, destination_name, GameState):
        if GameState.world_data is None:
            raise ValueError('GameState.world_data has not been initialized!')
        self.origin_name = origin_name
        self.origin_importance = int(GameState.world_data[origin_name].importance().strip("{} ").strip("'"))
        self.destination_name = destination_name
        self.destination_importance = int(GameState.world_data[destination_name].importance().strip("{} ").strip("'"))
        if self.origin_importance <= (self.destination_importance + 2):
            raise ValueError('Destination World must be at least Importance-2 less than origin world')
        self.serial = str(uuid.uuid4())