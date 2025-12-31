"""A class that represents one mail shipment from T5, p220"""

import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from t5code.GameState import GameState


class T5Mail:
    def __init__(self,
                 origin_name: str,
                 destination_name: str,
                 game_state: "GameState") -> None:
        if game_state.world_data is None:
            raise ValueError("GameState.world_data has not been initialized!")
        self.origin_name: str = origin_name
        self.destination_name: str = destination_name
        # Shortcuts to world data
        world_data = game_state.world_data
        origin_world = world_data[origin_name]
        destination_world = world_data[destination_name]

        self.origin_importance: int = int(origin_world.importance()
                                          .strip("{} ").strip("'"))

        self.destination_importance: int = int(
            destination_world.importance().strip("{} ").strip("'")
        )
        # Validate route logic (origin must be significantly more important)
        if self.origin_importance <= (self.destination_importance + 2):
            raise ValueError(
                "Destination World must be at least Importance-2 "
                "less than origin world"
            )

        self.serial: str = str(uuid.uuid4())
