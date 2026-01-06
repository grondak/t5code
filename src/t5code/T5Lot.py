"""Trade lot representation for Traveller 5 speculative cargo.

A lot represents a batch of trade goods from one world, with origin value,
market value, tech level, and trade classifications. Implements T5 Book 2 p209
rules for speculative cargo trading.
"""

import uuid
import random
from typing import TYPE_CHECKING, Dict, Tuple

from t5code.T5Tables import (
    BUYING_GOODS_TRADE_CLASSIFICATIONS_TABLE,
    SELLING_GOODS_TRADE_CLASSIFICATIONS_TABLE,
    ACTUAL_VALUE,
)
from t5code.T5Basics import (
    letter_to_tech_level,
    tech_level_to_letter,
    SequentialFlux
)

if TYPE_CHECKING:
    from t5code.GameState import GameState
    from t5code.T5World import T5World


class T5Lot:
    """Speculative cargo lot for trading between worlds.

    Implements 100% RAW (Rules As Written)
    T5 lot mechanics from T5 Book 2 p209.
    Each lot has an origin world, value, mass, and trade characteristics that
    determine purchase cost and sale price at different markets.

    Attributes:
        serial: Unique UUID identifier for this lot
        origin_name: Name of world where lot originates
        origin_uwp: Universal World Profile of origin world
        origin_tech_level: Tech level of origin (0-15+)
        origin_trade_classifications: Space-separated trade codes
        origin_value: Base value per ton in credits
        mass: Size of lot in tons
        lot_id: Human-readable identifier (format: "TL-Codes Value")

    Example:
        >>> from t5code import T5Lot, GameState
        >>> game_state = GameState(...)
        >>> lot = T5Lot("Rhylanor", game_state)
        >>> lot.mass = 10
        >>> print(f"Lot value: Cr{lot.origin_value * lot.mass:,}")
    """

    def __eq__(self, other: object) -> bool:
        return isinstance(other, T5Lot) and self.serial == other.serial

    def __hash__(self) -> int:
        return hash(self.serial)

    def __init__(self, origin_name: str, game_state: "GameState") -> None:
        """Create a new trade lot from an origin world.

        Automatically determines tech level, trade codes, and base value
        from the origin world's data.

        Args:
            origin_name: Name of the world producing this lot
            game_state: GameState instance with initialized world_data

        Raises:
            ValueError: If GameState.world_data is not initialized
        """
        # Basic identity
        self.size: int = 10
        self.origin_name: str = origin_name

        # Verify GameState is initialized
        from t5code.GameState import GameState
        GameState.validate_world_data(game_state)

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
        """Calculate sale value of this lot on a specific market world.

        Uses T5 formula: Base value × (1 + 0.1 × (Origin TL - Market TL))
        then applies trade classification bonuses/penalties from selling table.

        Args:
            market_world: Name of world where lot is being sold
            game_state: GameState with initialized world_data

        Returns:
            Sale value in credits for the entire lot
        """
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

    def calculate_profit_at(self,
                            destination_world: str,
                            game_state: "GameState") -> Tuple[int, int, int]:
        """Calculate profit/loss for selling this lot at destination.

        Computes purchase price (origin_value × mass), sale value at
        destination, and profit (sale - purchase). Useful for
        evaluating cargo deals before purchase.

        Args:
            destination_world: Name of world where lot would be sold
            game_state: GameState with initialized world_data

        Returns:
            Tuple of (purchase_price, sale_value, profit):
            - purchase_price: Cost to buy lot (credits)
            - sale_value: Revenue from selling (credits)
            - profit: Net profit/loss (credits, can be negative)

        Example:
            >>> lot = T5Lot("Rhylanor", game_state)
            >>> lot.mass = 10
            >>> purchase, sale, profit = lot.calculate_profit_at(
            ...     "Jae Tellona", game_state)
            >>> if profit > 0:
            ...     print(f"Profitable: Cr{profit}")
        """
        purchase_price = self.origin_value * self.mass
        sale_value = self.determine_sale_value_on(
            destination_world, game_state
        )
        profit = sale_value - purchase_price
        return purchase_price, sale_value, profit

    def generate_lot_id(self) -> str:
        """Generate human-readable lot identifier.

        Format: "TL-TradeCodes Value"
        Example: "A-Ag Ri 8500" (Tech level A, Agricultural Rich, Cr8500/ton)

        Returns:
            Lot ID string
        """
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
        """Generate random lot mass using log-normal distribution.

        Uses log-normal distribution to create realistic cargo lot sizes,
        with most lots being small but occasional large shipments.

        Args:
            mu: Mean of underlying normal distribution (default 2.6)
            sigma: Standard deviation of underlying normal (default 0.7)
            min_mass: Minimum lot size in tons (default 1)
            max_mass: Maximum lot size in tons (default 100)

        Returns:
            Lot mass in tons (integer)

        Note:
            Blocks until a value within [min_mass, max_mass] is generated.
        """
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
        """Calculate base cost per ton of a lot.

        Combines base cost (Cr3000) with modifiers from trade classifications
        and tech level.

        Args:
            trade_classifications: Space-separated trade codes (e.g., "Ag Ri")
            trade_classifictions_table: Modifier table for buying
            tech_level: Tech level of origin world (0-15+)

        Returns:
            Cost per ton in credits
        """
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
        """Calculate total modifier from trade classifications when buying.

        Sums up all modifiers from matching trade codes in the buying table.

        Args:
            trade_classifications: Space-separated trade codes
            trade_classifictions_table: Buying modifiers table

        Returns:
            Total credit modifier (can be positive or negative)
        """
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
        """Calculate selling bonus when origin goods match market needs.

        Awards Cr1000 per matching pair: origin trade code → market needs.
        Uses the selling table to determine which origin goods are valuable
        on which destination markets.

        Args:
            market_world: Destination market world
            origin_trade_classifications: Trade codes from lot's origin
            selling_goods_trade_classifications_table:
                Origin→Destination mapping

        Returns:
            Total credit bonus (Cr1000 per match)
        """
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
        """Filter trade classifications to only allowed codes.

        Keeps only those trade codes that appear in both the provided
        list and the allowed list. Used to exclude certain trade codes
        from lot value calculations.

        Args:
            provided_trade_classifications: Space-separated
            trade codes from world
            allowed_trade_classifications: Space-separated allowed codes

        Returns:
            Space-separated string of codes present in both lists
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

    def predict_actual_value_range(
        self, mod: int, sequential_flux: SequentialFlux = None
    ) -> Tuple[float, float, SequentialFlux]:
        """
        Use Trader skill to predict the range of actual values by rolling
        one die early. This implements the T5 Trader skill mechanic from
        p221: "Use of Trader skill allows one die on the Actual Value Table
        to be thrown early."

        Args:
            mod: Broker modifier to apply to flux roll
            sequential_flux: Optional pre-rolled SequentialFlux. If None,
                           rolls a new first die.

        Returns:
            Tuple of (min_multiplier, max_multiplier, sequential_flux)
            where multipliers are from ACTUAL_VALUE table and sequential_flux
            can be used to complete the roll later.

        Example:
            # Trader checks market before selling
            min_val, max_val, flux = lot.predict_actual_value_range(broker_mod)
            print(f"Price will be {min_val*100}% to {max_val*100}%")

            if min_val >= 1.0:
                # Good deal, complete the sale
                final_flux = flux.roll_second()
                actual = ACTUAL_VALUE[max(-5, min(8, final_flux + broker_mod))]
        """
        if sequential_flux is None:
            sequential_flux = SequentialFlux()

        # Get the potential flux range from the first die
        min_flux, max_flux = sequential_flux.potential_range

        # Apply modifier and clamp to ACTUAL_VALUE table bounds
        min_flux_modded = max(-5, min(8, min_flux + mod))
        max_flux_modded = max(-5, min(8, max_flux + mod))

        # Look up multipliers in ACTUAL_VALUE table
        min_multiplier = ACTUAL_VALUE[min_flux_modded]
        max_multiplier = ACTUAL_VALUE[max_flux_modded]

        return (min_multiplier, max_multiplier, sequential_flux)
