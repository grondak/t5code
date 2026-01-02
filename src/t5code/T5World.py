"""World representation and trade operations for Traveller 5.

This module provides the T5World class for representing planets and starports,
including passenger availability,
freight capacity, and speculative cargo generation.
Also includes utilities for finding the best broker at a given starport.
"""

from typing import Dict, Any, List, TYPE_CHECKING
from t5code.T5Basics import roll_flux
from t5code.T5Tables import BROKERS

if TYPE_CHECKING:
    from t5code.T5Lot import T5Lot
    from t5code.GameState import GameState


def find_best_broker(starport_tier: str) -> Dict[str, Any]:
    """Find the best available broker at a starport.

    Brokers have different skill modifiers and fee rates depending on starport
    quality. This function returns the broker with the highest skill modifier
    available at the given starport tier.

    Args:
        starport_tier: Starport quality class ('A', 'B', 'C', or 'D')

    Returns:
        Dictionary with keys:
            - name (str): Broker's title
            - mod (int): Skill modifier
            - rate (float): Fee rate as decimal (e.g., 0.05 for 5%)

    Raises:
        ValueError: If starport_tier is not one of 'A', 'B', 'C', 'D'

    Example:
        >>> broker = find_best_broker('A')
        >>> print(f"{broker['name']} charges {broker['rate']*100}% fees")
        Master Merchant charges 5.0% fees
    """
    # Handle invalid/non-standard starport tiers
    if starport_tier not in {"A", "B", "C", "D"}:
        # Default to D tier for non-standard starports (E, X, etc.)
        starport_tier = "D"

    best_name = None
    best_mod = -1
    best_rate = None

    for name, (tiers, mod, rate) in BROKERS.items():
        if starport_tier in tiers and mod > best_mod:
            best_name = name
            best_mod = mod
            best_rate = rate

    return {
        "name": best_name,
        "mod": best_mod,
        "rate": best_rate,
    }


class T5World:
    """Represents a world in the Traveller 5 universe.

    A world includes its Universal World Profile (UWP), trade classifications,
    importance rating, and methods for generating passengers, freight, and
    speculative cargo based on T5 rules.

    Attributes:
        name: World name
        world_data: Dictionary containing UWP,
           trade classifications, and importance

    Example:
        >>> world_data = {"Rhylanor": {"UWP": "A788899-A", ...}}
        >>> world = T5World("Rhylanor", world_data)
        >>> print(world.get_starport())  # 'A'
        >>> print(world.get_population())  # 8
    """

    def __init__(self,
                 name: str,
                 world_data: Dict[str, Dict[str, Any]]) -> None:
        """Initialize a T5World instance.

        Args:
            name: Name of the world
            world_data: Dictionary mapping world names to their data dicts,
                which must include 'UWP',
                'TradeClassifications', and 'Importance'

        Raises:
            ValueError: If the specified world name is not in world_data
        """
        self.name: str = name
        if name in world_data:
            self.world_data: Dict[str, Any] = world_data[name]
        else:
            raise ValueError(f"Specified world {name} is "
                             "not in provided worlds table")

    def uwp(self) -> str:
        """Get the Universal World Profile string.

        Returns:
            UWP string (e.g., 'A788899-A' for a high-tech industrial world)
        """
        return self.world_data["UWP"]

    def trade_classifications(self) -> str:
        """Get trade classification codes.

        Returns:
            Space-separated trade codes
            (e.g., 'Ag Ri' for agricultural rich world)
        """
        return self.world_data["TradeClassifications"]

    def importance(self) -> str:
        """Get world importance rating.

        Returns:
            Importance value as string (e.g., '+2', '-1')
        """
        return self.world_data["Importance"]

    @staticmethod
    def load_all_worlds(
        world_data: Dict[str,
                         Dict[str,
                              Any]]) -> Dict[str, "T5World"]:
        """Create T5World instances for all worlds in the data.

        Args:
            world_data: Dictionary mapping world names to their data

        Returns:
            Dictionary mapping world names to T5World instances
        """
        return {name: T5World(name, world_data) for name,
                data in world_data.items()}

    def get_starport(self) -> str:
        """Extract starport class from UWP.

        Returns:
            Starport class letter ('A' through 'E', or 'X' for no starport)
        """
        return self.uwp()[0:1]

    def get_population(self) -> int:
        """Extract population digit from UWP.

        Returns:
            Population code (0-15), where higher values indicate more people.
            Handles hex digits (A=10, B=11, etc.)
        """
        pop_char = self.uwp()[4:5]
        try:
            # Try standard int conversion first (0-9)
            return int(pop_char)
        except ValueError:
            # Handle hex digits (A-F)
            return int(pop_char, 16)

    TRADE_CODE_MULTIPLIER_TAGS = {
        "Ag",  # Agricultural
        "As",  # Asteroid
        "Ba",  # Barren
        "De",  # Desert
        "Fl",  # Fluid Oceans
        "Hi",  # High Population
        "Ic",  # Ice-Capped
        "In",  # Industrial
        "Lo",  # Low Population
        "Na",  # Non-Agricultural
        "Ni",  # Non-Industrial
        "Po",  # Poor
        "Ri",  # Rich
        "Va",  # Vacuum
    }

    def freight_lot_mass(self, liaison_bonus: int) -> int:
        """Calculate available freight lot mass in tons.

        Uses flux + population, doubled if world has certain trade codes.
        Represents how much freight is available on a given day.

        Args:
            liaison_bonus: Modifier from crew's Liaison skill

        Returns:
            Mass of freight lot in tons (minimum 0)

        Example:
            >>> world = T5World("Rhylanor", world_data)
            >>> mass = world.freight_lot_mass(liaison_bonus=2)
            >>> print(f"Available freight: {mass} tons")
        """
        flux = roll_flux()
        population = self.get_population()
        tags = set(self.trade_classifications())
        multiplier = 1 + int(bool(tags & self.TRADE_CODE_MULTIPLIER_TAGS))

        mass = (flux + population) * multiplier + liaison_bonus
        return max(mass, 0)

    def high_passenger_availability(self, steward_skill: int) -> int:
        """Determine number of available high passengers.

        Args:
            steward_skill: Steward skill modifier

        Returns:
            Number of high passengers available (Cr10,000 each)
        """
        flux = roll_flux()
        population = self.get_population()
        available = flux + population + steward_skill
        return max(available, 0)

    def mid_passenger_availability(self, admin_skill: int) -> int:
        """Determine number of available mid passengers.

        Args:
            admin_skill: Admin skill modifier

        Returns:
            Number of mid passengers available (Cr8,000 each)
        """
        flux = roll_flux()
        population = self.get_population()
        available = flux + population + admin_skill
        return max(available, 0)

    def low_passenger_availability(self, streetwise_skill: int) -> int:
        """Determine number of available low passengers.

        Args:
            streetwise_skill: Streetwise skill modifier

        Returns:
            Number of low passengers available (Cr1,000 each)
        """
        flux = roll_flux()
        population = self.get_population()
        available = flux + population + streetwise_skill
        return max(available, 0)

    def generate_speculative_cargo(
        self,
        game_state: "GameState",
        max_total_tons: int = 100,
        max_lot_size: int = 10
    ) -> List["T5Lot"]:
        """Generate speculative cargo lots available for purchase.

        In Traveller, up to 100 tons of cargo are available for purchase
        in multiple lots when captains want to leave "soon" rather than
        waiting for freight (which can take many days to accumulate).

        Args:
            game_state: GameState instance for creating lots
            max_total_tons: Maximum total tonnage available (default 100)
            max_lot_size: Maximum size of individual lots (default 10)

        Returns:
            List of T5Lot instances totaling exactly max_total_tons
        """
        from t5code.T5Lot import T5Lot

        lots: List[T5Lot] = []
        total_mass = 0

        while total_mass < max_total_tons:
            # Create a lot from this world
            lot = T5Lot(self.name, game_state)

            # Constrain lot size to not exceed
            # max_lot_size or remaining capacity
            remaining = max_total_tons - total_mass

            if remaining <= max_lot_size:
                # Last lot - use exactly the remaining space
                lot.mass = remaining
            else:
                # Generate random lot size within constraints
                lot.mass = lot.generate_lot_mass(
                    min_mass=1,
                    max_mass=max_lot_size
                )

            total_mass += lot.mass
            lots.append(lot)

        return lots
