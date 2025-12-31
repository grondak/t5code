"""A class that represents one lot from Traveller 5.
   A lot is a batch of goods for sale from one world, p209."""

import uuid
import random
from typing import TYPE_CHECKING, Dict

from t5code.T5Tables import (
    BUYING_GOODS_TRADE_CLASSIFICATIONS_TABLE,
    SELLING_GOODS_TRADE_CLASSIFICATIONS_TABLE,
    ACTUAL_VALUE,
)
from t5code.T5Basics import letter_to_tech_level, tech_level_to_letter

if TYPE_CHECKING:
    from t5code.GameState import GameState
    from t5code.T5World import T5World


class T5Lot:
    """100% RAW T5 Lot, see T5Book 2 p209."""

    def __eq__(self, other: object) -> bool:
        return isinstance(other, T5Lot) and self.serial == other.serial

    def __hash__(self) -> int:
        return hash(self.serial)

    def __init__(self, origin_name: str, game_state: "GameState") -> None:
        # Basic identity
        self.size: int = 10
        self.origin_name: str = origin_name

        # Verify GameState is initialized
        if game_state.world_data is None:
            raise ValueError("GameState.world_data has not been initialized!")

        # Lookup world data
        world = game_state.world_data[origin_name]

        # Extract UWP and Tech Level
        self.origin_uwp: str = world.uwp()
        self.origin_tech_level: int = letter_to_tech_level(self.origin_uwp[8:])

        # Filter valid trade classifications
        self.origin_trade_classifications: str = (
            T5Lot.filter_trade_classifications(
                world.trade_classifications(),
                " ".join(
                    BUYING_GOODS_TRADE_CLASSIFICATIONS_TABLE.keys()
                ),
            )
        )

        # Calculate value based on origin attributes
        self.origin_value: int = T5Lot.determine_lot_cost(
            self.origin_trade_classifications,
            BUYING_GOODS_TRADE_CLASSIFICATIONS_TABLE,
            self.origin_tech_level,
        )

        # Metadata and identifiers
        self.lot_id: str = self.generate_lot_id()
        self.mass: int = self.generate_lot_mass()
        self.serial: str = str(uuid.uuid4())

    def determine_sale_value_on(self,
                                market_world: str,
                                game_state: "GameState") -> int:
        """10% x Source TL minus Market TL + table effects"""
        tl_adjustment: float = 0.1 * (
            self.origin_tech_level
            - letter_to_tech_level(
                game_state.world_data[market_world].uwp()[8:])
        )
        result = round(
            max((1 + tl_adjustment), 0)
            * (
                5000
                + T5Lot.determine_selling_trade_classifications_effects(
                    game_state.world_data[market_world],
                    self.origin_trade_classifications,
                    SELLING_GOODS_TRADE_CLASSIFICATIONS_TABLE,
                )
            )
        )
        return result

    def generate_lot_id(self) -> str:
        result = (
            tech_level_to_letter(self.origin_tech_level)
            + (
                ("-" + self.origin_trade_classifications)
                if self.origin_trade_classifications
                else ""
            )
            + " "
            + str(self.origin_value)
        )
        return result

    def generate_lot_mass(self,
                          mu: float = 2.6,
                          sigma: float = 0.7,
                          min_mass: int = 1,
                          max_mass: int = 100) -> int:
        while True:
            # random.lognormvariate provides similar behaviour without
            # requiring the numpy dependency
            lot = random.lognormvariate(mu, sigma)
            if min_mass <= lot <= max_mass:
                return int(round(lot))

    @staticmethod
    def determine_lot_cost(
        trade_classifications: str,
        trade_classifictions_table: Dict[str, int],
        tech_level: int
    ) -> int:
        result = (
            3000
            + T5Lot.determine_buying_trade_classifications_effects(
                trade_classifications, trade_classifictions_table
            )
            + tech_level * 100
        )
        return result

    @staticmethod
    def determine_buying_trade_classifications_effects(
        trade_classifications: str, trade_classifictions_table: Dict[str, int]
    ) -> int:
        effect = 0
        for classification in trade_classifications.split():
            if classification in trade_classifictions_table:
                effect += trade_classifictions_table[classification]
        return effect

    @staticmethod
    def determine_selling_trade_classifications_effects(
        market_world: "T5World",
        origin_trade_classifications: str,
        selling_goods_trade_classifications_table: Dict[str, str],
    ) -> int:
        effect = 0
        table = selling_goods_trade_classifications_table
        for origin_classification in origin_trade_classifications.split():
            if table[origin_classification] is not None:
                for selling_classification in table[
                    origin_classification
                ].split():
                    if (
                        selling_classification
                        in market_world.trade_classifications().split()
                    ):
                        effect += 1000
        return effect

    @staticmethod
    def filter_trade_classifications(
        provided_trade_classifications: str, allowed_trade_classifications: str
    ) -> str:
        """
        Filters provided trade classifications based
        on the allowed trade classifications.

        Args:
            provided_trade_classifications (str): A space-separated string
               of provided classifications.
            allowed_trade_classifications (str): A space-separated string
               of allowed classifications.

        Returns:
            str: A space-separated string of classifications that
               are both provided and allowed.
        """
        provided_set = set(
            provided_trade_classifications.split()
        )  # Convert to set for quick lookup
        allowed_set = set(
            allowed_trade_classifications.split()
        )  # Convert to set for quick lookup

        # Find the intersection of provided and allowed classifications
        filtered_set = provided_set.intersection(allowed_set)

        # Convert the result back to a space-separated string
        return " ".join(sorted(filtered_set))  # Sorting ensures output order

    def consult_actual_value_table(self, mod: int) -> float:
        """
        Roll Flux (1d6 - 1d6), apply modifier, clamp result [-5, 8],
        and return the corresponding actual value from T5Tables.
        """
        die1 = random.randint(1, 6)
        die2 = random.randint(1, 6)
        raw_flux = die1 - die2
        modded_flux = raw_flux + mod

        clamped_flux = max(-5, min(8, modded_flux))
        return ACTUAL_VALUE[clamped_flux]
