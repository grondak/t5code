class T5ShipClass:
    """A starship class intended to implement just enough of the
    T5 Starship concepts to function in the simulator"""

    def __init__(self, class_name, ship_data):
        self.class_name = class_name
        self.jump_rating = ship_data["jump_rating"]
        self.maneuver_rating = ship_data["maneuver_rating"]
        self.cargo_capacity = ship_data["cargo_capacity"]

    def usp(self):
        return (
            f"{self.class_name} "
            f"{self.jump_rating}"
            f"{self.maneuver_rating}\n"
            f"Cargo: {self.cargo_capacity} tons"
        )

    @staticmethod
    def load_all_ship_classes(ship_data):
        return {
            class_name: T5ShipClass(class_name, data)
            for class_name, data in ship_data.items()
        }
