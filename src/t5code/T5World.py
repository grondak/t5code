"""A class that represents one World from Traveller 5."""

from typing import Dict, Any
from t5code.T5Basics import roll_flux
from t5code.T5Tables import BROKERS


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
