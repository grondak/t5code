"""A class that represents one World from Traveller 5."""

from typing import Dict, Any, List, TYPE_CHECKING
from t5code.T5Basics import roll_flux
from t5code.T5Tables import BROKERS

if TYPE_CHECKING:
    from t5code.T5Lot import T5Lot
    from t5code.GameState import GameState


def find_best_broker(starport_tier: str) -> Dict[str, Any]:
    if starport_tier not in {"A", "B", "C", "D"}:
        raise ValueError("Tier must be one of: 'A', 'B', 'C', 'D'")

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
    def __init__(self,
                 name: str,
                 world_data: Dict[str, Dict[str, Any]]) -> None:
        self.name: str = name
        if name in world_data:
            self.world_data: Dict[str, Any] = world_data[name]
        else:
            raise ValueError(f"Specified world {name} is "
                             "not in provided worlds table")

    def uwp(self) -> str:
        return self.world_data["UWP"]

    def trade_classifications(self) -> str:
        return self.world_data["TradeClassifications"]

    def importance(self) -> str:
        return self.world_data["Importance"]

    @staticmethod
    def load_all_worlds(
        world_data: Dict[str,
                         Dict[str,
                              Any]]) -> Dict[str, "T5World"]:
        return {name: T5World(name, world_data) for name,
                data in world_data.items()}

    def get_starport(self) -> str:
        return self.uwp()[0:1]

    def get_population(self) -> int:
        return int(self.uwp()[4:5])

    TRADE_CODE_MULTIPLIER_TAGS = {
        "Ag",
        "As",
        "Ba",
        "De",
        "Fl",
        "Hi",
        "Ic",
        "In",
        "Lo",
        "Na",
        "Ni",
        "Po",
        "Ri",
        "Va",
    }

    def freight_lot_mass(self, liaison_bonus: int) -> int:
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
