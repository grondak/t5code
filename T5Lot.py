"""A class that represents one lot from Traveller 5."""

from T5Tables import *
from T5Basics import *
import numpy as np
import uuid


class T5Lot:
    """100% RAW T5 Lot, see T5Book 2 p209."""

    def __eq__(self, other):
        return isinstance(other, T5Lot) and self.serial == other.serial

    def __hash__(self):
        return hash(self.serial)

    def __init__(self, origin_name, GameState):
        self.size = 10
        self.origin_name = origin_name
        if GameState.world_data is None:
            raise ValueError("GameState.world_data has not been initialized!")
        self.origin_UWP = GameState.world_data[origin_name].UWP()
        self.origin_tech_level = letter_to_tech_level(self.origin_UWP[8:])
        self.origin_trade_classifications = T5Lot.filter_trade_classifications(
            GameState.world_data[origin_name].trade_classifications(),
            " ".join(T5Tables.buying_goods_trade_classifications_table.keys()),
        )
        self.origin_value = T5Lot.determine_lot_cost(
            self.origin_trade_classifications,
            T5Tables.buying_goods_trade_classifications_table,
            self.origin_tech_level,
        )
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
                    T5Tables.selling_goods_trade_classifications_table,
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

    def generate_lot_mass(self):
        # Parameters for the log-normal distribution
        mu = 2.6  # Mean of the log (adjust to center around 15-20 tons)
        sigma = 0.7  # Standard deviation of the log (adjust for tail weight)

        # Generate random cargo lots
        lots = np.random.lognormal(mean=mu, sigma=sigma, size=1)

        # Filter lots to a minimum of 1 ton and max of 100 tons
        lots = lots[lots >= 1]
        lots = lots[lots <= 100]
        # Truncate the lots to ensure a minimum of 1 ton and clip to integers
        lots = np.clip(lots, a_min=1, a_max=None)  # Ensure minimum of 1 ton
        lots = np.rint(lots).astype(int)  # Round to nearest integer
        return int(lots[0])

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
