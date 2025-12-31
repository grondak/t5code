"""Ship class definitions for Traveller 5 starships.

Defines the T5ShipClass class for representing starship types with
jump rating, maneuver rating, and cargo capacity.
"""

from typing import Dict, Any


class T5ShipClass:
    """A starship class intended to implement just enough of the
    T5 Starship concepts to function in the simulator"""

    def __init__(self, class_name: str, ship_data: Dict[str, Any]) -> None:
        self.class_name: str = class_name
        self.jump_rating: int = ship_data["jump_rating"]
        self.maneuver_rating: float = ship_data["maneuver_rating"]
        self.cargo_capacity: int = ship_data["cargo_capacity"]

    def usp(self) -> str:
        return (
            f"{self.class_name} "
            f"{self.jump_rating}"
            f"{self.maneuver_rating}\n"
            f"Cargo: {self.cargo_capacity} tons"
        )

    @staticmethod
    def load_all_ship_classes(
        ship_data: Dict[str,
                        Dict[str,
                             Any]]) -> Dict[str, "T5ShipClass"]:
        return {
            class_name: T5ShipClass(class_name, data)
            for class_name, data in ship_data.items()
        }
