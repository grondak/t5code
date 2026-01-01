"""Mail shipment representation for Traveller 5.

Mail contracts (T5 p220) transport message containers between worlds.
Routes are restricted by world importance - mail only goes from more
important worlds to less important ones.
"""

import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from t5code.GameState import GameState


class T5Mail:
    """Mail container for interstellar message transport.

    Mail provides reliable income for starships but has strict route
    requirements: origin must be at least 2 importance levels higher
    than destination.

    Attributes:
        origin_name: Starting world name
        destination_name: Destination world name
        origin_importance: Origin world importance rating
        destination_importance: Destination world importance rating
        serial: Unique UUID identifier

    Example:
        >>> mail = T5Mail("Rhylanor", "Jae Tellona", game_state)
        >>> ship.onload_mail(mail)  # Cr25,000 payment
    """

    def __init__(self,
                 origin_name: str,
                 destination_name: str,
                 game_state: "GameState") -> None:
        """Create a mail shipment.

        Args:
            origin_name: Origin world (must be more important)
            destination_name: Destination world (must be less important)
            game_state: GameState with initialized world_data

        Raises:
            ValueError: If GameState.world_data not initialized
            ValueError: If origin importance <= destination importance + 2
        """
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
