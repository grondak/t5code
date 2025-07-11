"""A class that represents one lot from Traveller 5."""

import uuid
import random

from t5code.T5Tables import (
    BUYING_GOODS_TRADE_CLASSIFICATIONS_TABLE,
    SELLING_GOODS_TRADE_CLASSIFICATIONS_TABLE,
    ACTUAL_VALUE,
)
from t5code.T5Basics import letter_to_tech_level, tech_level_to_letter


class T5Lot:
    """100% RAW T5 Lot, see T5Book 2 p209."""

    def __eq__(self, other):
        return isinstance(other, T5Lot) and self.serial == other.serial

    def __hash__(self):
        return hash(self.serial)

    def __init__(self, origin_name, GameState):
        # Basic identity
        self.size = 10
        self.origin_name = origin_name

        # Verify GameState is initialized
        if GameState.world_data is None:
            raise ValueError("GameState.world_data has not been initialized!")

        # Lookup world data
        world = GameState.world_data[origin_name]

        # Extract UWP and Tech Level
        self.origin_UWP = world.UWP()
        self.origin_tech_level = letter_to_tech_level(self.origin_UWP[8:])

        # Filter valid trade classifications
        self.origin_trade_classifications = T5Lot.filter_trade_classifications(
            world.trade_classifications(),
            " ".join(BUYING_GOODS_TRADE_CLASSIFICATIONS_TABLE.keys()),
        )

        # Calculate value based on origin attributes
        self.origin_value = T5Lot.determine_lot_cost(
            self.origin_trade_classifications,
            BUYING_GOODS_TRADE_CLASSIFICATIONS_TABLE,
            self.origin_tech_level,
        )

        # Metadata and identifiers
        self.lot_id = self.generate_lot_id()
        self.mass = self.generate_lot_mass()
        self.serial = str(uuid.uuid4())

    def determine_sale_value_on(self, marketWorld, GameState):
        """10% x Source TL minus Market TL + table effects"""
        TL_adjustment = 0.1 * (
            self.origin_tech_level
            - letter_to_tech_level(GameState.world_data[marketWorld].UWP()[8:])
        )
        result = round(
            max((1 + TL_adjustment), 0)
            * (
                5000
                + T5Lot.determine_selling_trade_classifications_effects(
                    GameState.world_data[marketWorld],
                    self.origin_trade_classifications,
                    SELLING_GOODS_TRADE_CLASSIFICATIONS_TABLE,
                )
            )
        )
        return result

    def generate_lot_id(self):
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

    def generate_lot_mass(self, mu=2.6, sigma=0.7, min_mass=1, max_mass=100):
        while True:
            # random.lognormvariate provides similar behaviour without
            # requiring the numpy dependency
            lot = random.lognormvariate(mu, sigma)
            if min_mass <= lot <= max_mass:
                return int(round(lot))

    def determine_lot_cost(
        trade_classifications, trade_classifictions_table, tech_level
    ):
        result = (
            3000
            + T5Lot.determine_buying_trade_classifications_effects(
                trade_classifications, trade_classifictions_table
            )
            + tech_level * 100
        )
        return result

    def determine_buying_trade_classifications_effects(
        trade_classifications, trade_classifictions_table
    ):
        effect = 0
        for classification in trade_classifications.split():
            if classification in trade_classifictions_table:
                effect += trade_classifictions_table[classification]
        return effect

    def determine_selling_trade_classifications_effects(
        marketWorld,
        origin_trade_classifications,
        selling_goods_trade_classifications_table,
    ):
        effect = 0
        for origin_classification in origin_trade_classifications.split():
            if selling_goods_trade_classifications_table[origin_classification] != None:
                for selling_classification in selling_goods_trade_classifications_table[
                    origin_classification
                ].split():
                    if (
                        selling_classification
                        in marketWorld.trade_classifications().split()
                    ):
                        effect += 1000
        return effect

    def filter_trade_classifications(
        provided_trade_classifications, allowed_trade_classifications
    ):
        """
        Filters provided trade classifications based on the allowed trade classifications.

        Args:
            provided_trade_classifications (str): A space-separated string of provided classifications.
            allowed_trade_classifications (str): A space-separated string of allowed classifications.

        Returns:
            str: A space-separated string of classifications that are both provided and allowed.
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
        return " ".join(sorted(filtered_set))  # Sorting ensures consistent output order

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
