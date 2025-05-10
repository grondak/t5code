import csv


class T5ShipClass:
    """A starship class intended to implement just enough of the T5 Starship concepts to function in the simulator"""

    def __init__(self, class_name, ship_data):
        self.className = class_name
        self.jumpRating = ship_data["jump_rating"]
        self.maneuverRating = ship_data["maneuver_rating"]
        self.cargoCapacity = ship_data["cargo_capacity"]

    def USP(self):
        return (
            f"{self.className} "
            f"{self.jumpRating}"
            f"{self.maneuverRating}\n"
            f"Cargo: {self.cargoCapacity} tons"
        )

    def load_all_ship_classes(ship_data):
        return {
            class_name: T5ShipClass(class_name, data)
            for class_name, data in ship_data.items()
        }
