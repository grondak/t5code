"""A class that represents one World from Traveller 5."""

import T5Code.T5Basics


class T5World:
    def __init__(self, name, world_data):
        self.name = name
        if name in world_data:
            self.world_data = world_data[name]
        else:
            raise ValueError(f"Specified world {name} is not in provided worlds table")

    def UWP(self):
        return self.world_data["UWP"]

    def trade_classifications(self):
        return self.world_data["TradeClassifications"]

    def importance(self):
        return self.world_data["Importance"]

    def load_all_worlds(world_data):
        return {name: T5World(name, world_data) for name, data in world_data.items()}
