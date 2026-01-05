"""Ship class definitions for Traveller 5 starships.

Defines the T5ShipClass class for representing starship design specifications
including performance ratings and capacity limits.
"""

from typing import Dict, Any, List


class T5ShipClass:
    """Starship design specification with performance and capacity.

    Represents a class of starship (e.g., "Free Trader", "Scout") with
    standard specifications for jump capability, maneuverability, and
    cargo/passenger capacity.

    Attributes:
        class_name: Ship class designation
        jump_rating: Jump drive rating (parsecs per jump, typically 1-6)
        maneuver_rating: Maneuver drive rating (typically 1-6)
        cargo_capacity: Hold size in tons
        staterooms: Number of passenger/crew staterooms
        low_berths: Number of low berth pods
        crew_positions: List of crew position codes (e.g., ['A', 'B', 'C'])

    Example:
        >>> ship_class = T5ShipClass("Free Trader", {
        ...     "jump_rating": 1,
        ...     "maneuver_rating": 1,
        ...     "cargo_capacity": 82,
        ...     "staterooms": 10,
        ...     "low_berths": 20
        ... })
    """

    def __init__(self, class_name: str, ship_data: Dict[str, Any]) -> None:
        """Create ship class from specification data.

        Args:
            class_name: Name/designation of ship class
            ship_data: Dictionary with required keys: jump_rating,
                maneuver_rating, cargo_capacity, staterooms, low_berths
                Optional: powerplant_rating (defaults to maneuver_rating)
        """
        self.class_name: str = class_name
        self.jump_rating: int = ship_data["jump_rating"]
        self.maneuver_rating: float = ship_data["maneuver_rating"]
        self.powerplant_rating: int = ship_data.get("powerplant_rating",
                                                    self.maneuver_rating)
        self.cargo_capacity: int = ship_data["cargo_capacity"]
        self.staterooms: int = ship_data["staterooms"]
        self.low_berths: int = ship_data["low_berths"]
        self.crew_positions: List[str] = ship_data.get("crew_positions", [])

    def usp(self) -> str:
        """Generate Universal Ship Profile string.

        Returns:
            Multi-line string with class name, ratings, and cargo capacity
        """
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
        """Load all ship classes from data dictionary.

        Args:
            ship_data: Dictionary mapping class names to specification dicts

        Returns:
            Dictionary mapping class names to T5ShipClass instances
        """
        return {
            class_name: T5ShipClass(class_name, data)
            for class_name, data in ship_data.items()
        }
