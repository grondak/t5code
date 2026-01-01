"""Random trade goods generation for Traveller 5 cargo generation.

Provides tables and logic for generating random trade goods with pricing,
common classifications, and market dynamics.
"""

from typing import Union, Callable, List, Dict, Sequence, Any
import random
import json
from pathlib import Path

# Constants for table structure
TABLE_SIZE = 6  # All T5 trade tables have exactly 6 entries
DICE_MIN = 0
DICE_MAX = 5  # Corresponds to d6 (1-6) mapped to 0-5 index


class TradeGood:
    """Base class for trade good items.

    Represents a trade good with a name that can be either static
    or dynamically generated via a callable.

    Args:
        name: Static string or callable that returns a trade good name
    """

    def __init__(self, name: Union[str, Callable[[], str]]):
        self._name = name

    def get_name(self) -> str:
        """Get the trade good's name.

        Returns:
            Trade good name (calls name function if callable)
        """
        return self._name() if callable(self._name) else self._name


class ImbalanceTradeGood(TradeGood):
    """Special trade good representing market imbalance.

    When rolled, re-rolls on a specific classification table and provides
    a bonus if sold on a world matching that classification.

    Args:
        reroll_classification: Trade classification to re-roll on (e.g., "Ag")
        rtg_table: RandomTradeGoodsTable instance for re-rolling
    """

    def __init__(self, reroll_classification: str,
                 rtg_table: "RandomTradeGoodsTable"):
        self.reroll_classification = reroll_classification
        self.rtg_table = rtg_table
        super().__init__(self.resolve_name)

    def resolve_name(self) -> str:
        """Resolve the imbalance by re-rolling on classification table.

        Returns:
            Description including base good and bonus information
        """
        rerolled = self.rtg_table.get_random(self.reroll_classification)
        return f"Imbalance from {self.reroll_classification}: " \
            f"{rerolled} (+Cr1,000 if sold on {self.reroll_classification})"


class TradeGoodsTypeTable:
    """Table of 6 trade goods for a specific goods type.

    Each type (Common, Electronics, etc.) has exactly 6 goods that can
    be randomly selected via d6 roll.

    Args:
        type_name: Name of the trade goods type
        goods: Sequence of exactly 6 trade goods
            (strings, callables, or TradeGood instances)

    Raises:
        ValueError: If goods sequence doesn't have exactly 6 items
    """
    def __init__(self, type_name: str,
                 goods: Sequence[Union[str, Callable[[], str], "TradeGood"]]):
        if len(goods) != TABLE_SIZE:
            raise ValueError(f"{type_name} table must have "
                             f"exactly {TABLE_SIZE} trade goods.")
        self.type_name = type_name
        self.goods: List[TradeGood] = []
        for g in goods:
            if isinstance(g, TradeGood):
                self.goods.append(g)
            else:
                self.goods.append(TradeGood(g))

    def get_good(self, index: int) -> TradeGood:
        """Get a trade good by index (0-5).

        Args:
            index: Index into the goods table (0-5)

        Returns:
            Trade good at the specified index
        """
        return self.goods[index]

    def roll(self) -> TradeGood:
        """Roll d6 to get a random trade good.

        Returns:
            Random trade good from table (1d6)
        """
        return self.get_good(random.randint(DICE_MIN, DICE_MAX))


class TradeClassificationGoodsTable:
    """Trade goods table for a specific world classification.

    Organizes 6 type tables (Common, Electronics, etc.) for a classification.
    Each classification has 36 total goods (6 types × 6 goods each).

    Args:
        classification_code: World classification (e.g., "Ag", "In", "Na")

    Attributes:
        classification_code: The world classification code
        type_tables: Dictionary mapping type names to their tables
        type_order: Ordered list of type names for d6 rolls
    """

    def __init__(self, classification_code: str):
        self.classification_code = classification_code
        self.type_tables: Dict[str, TradeGoodsTypeTable] = {}
        self.type_order: List[str] = []

    def add_type_table(
        self,
        type_name: str,
        goods: Sequence[Union[str, Callable[[], str], "TradeGood"]]
    ):
        """Add a type table to this classification.

        Args:
            type_name: Name of goods type (e.g., "Common", "Electronics")
            goods: Sequence of 6 trade goods

        Raises:
            ValueError: If already have 6 type tables
        """
        if len(self.type_order) >= TABLE_SIZE:
            raise ValueError(
                f"Each classification may only "
                f"have {TABLE_SIZE} TradeGoodsTypeTables."
            )
        self.type_tables[type_name] = TradeGoodsTypeTable(type_name, goods)
        self.type_order.append(type_name)

    def get_good(self, type_name: str, index: int) -> TradeGood:
        """Get a specific trade good by type and index.

        Args:
            type_name: Name of goods type
            index: Index within that type's table (0-5)

        Returns:
            The specified trade good
        """
        return self.type_tables[type_name].get_good(index)

    def roll(self) -> TradeGood:
        """Roll 2d6 to get a random trade good.

        First d6 selects the type (Common, Electronics, etc.)
        Second d6 selects the specific good within that type.

        Returns:
            Random trade good from classification's 36 goods
        """
        type_index = random.randint(DICE_MIN, DICE_MAX)
        type_name = self.type_order[type_index]
        return self.type_tables[type_name].roll()


class RandomTradeGoodsTable:
    """Master table containing all trade classification tables.

    Manages the complete hierarchy of trade goods tables for all world
    classifications, enabling random goods generation and direct lookups.

    Attributes:
        classifications: Dictionary mapping
        classification codes to their tables
    """

    def __init__(self):
        self.classifications: Dict[str, TradeClassificationGoodsTable] = {}

    def add_classification_table(
        self, classification_code: str, table: TradeClassificationGoodsTable
    ):
        """Add a classification table to the master table.

        Args:
            classification_code: World classification code
            table: Complete classification goods table with 6 type tables
        """
        self.classifications[classification_code] = table

    def get_good(self,
                 classification: str,
                 type_name: str,
                 index: int) -> TradeGood:
        """Get a specific trade good by classification, type, and index.

        Args:
            classification: World classification code
            type_name: Goods type name
            index: Index within type table (0-5)

        Returns:
            The specified trade good
        """
        return self.classifications[classification].get_good(type_name, index)

    def get_random(self, classification: str) -> str:
        """Get a random trade good name for a classification.

        Rolls 2d6 to select type and good within that classification.

        Args:
            classification: World classification code

        Returns:
            Name of randomly selected trade good
        """
        return self.classifications[classification].roll().get_name()

    @classmethod
    def from_json(cls, json_path: Path) -> "RandomTradeGoodsTable":
        """Load trade goods tables from a JSON file.

        Constructs the complete hierarchy of trade goods tables from
        JSON data including classification tables, type tables, goods,
        imbalances, and classification aliases.

        Expected JSON structure:
        {
          "classifications": {
            "Ag-1": {
              "types": {
                "Raws": ["item1", "item2", ...],
                "Imbalances": [
                  {"type": "imbalance", "reroll_classification": "As"},
                  ...
                ]
              }
            },
            ...
          },
          "aliases": {
            "Ga": "Ag-1",
            ...
          }
        }

        Args:
            json_path: Path to JSON file containing trade goods data

        Returns:
            Fully populated RandomTradeGoodsTable with all classifications
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            data: Dict[str, Any] = json.load(f)

        table = cls()

        # First pass: Create all classification tables
        for (
            classification_code,
            classification_data
        ) in data["classifications"].items():
            classification_table = TradeClassificationGoodsTable(
                classification_code)

            for type_name, goods_data in classification_data["types"].items():
                goods: List[Union[str, TradeGood]] = []

                for item in goods_data:
                    if (
                        isinstance(item, dict)
                        and item.get("type") == "imbalance"
                    ):
                        # Create ImbalanceTradeGood for special entries
                        goods.append(ImbalanceTradeGood(
                            item["reroll_classification"],
                            table
                        ))
                    else:
                        # Regular string goods
                        goods.append(item)

                classification_table.add_type_table(type_name, goods)

            table.add_classification_table(
                classification_code,
                classification_table
            )

        # Second pass: Handle aliases (clones)
        if "aliases" in data:
            for alias_code, source_code in data["aliases"].items():
                source_table = table.classifications[source_code]
                clone_classification_table(alias_code, source_table, table)

        return table


def clone_classification_table(
    new_code: str,
    source_table: TradeClassificationGoodsTable,
    target_table: RandomTradeGoodsTable
) -> TradeClassificationGoodsTable:
    """Clone a classification table with a new code.

    Creates a new classification table that shares the same type tables
    and goods as the source, but with a different classification code.
    Used for implementing classification aliases (e.g., Ga → Ag).

    Args:
        new_code: New classification code for the clone
        source_table: Existing classification table to clone from
        target_table: Master table to register the clone in

    Returns:
        The newly created classification table
    """
    new_table = TradeClassificationGoodsTable(new_code)
    for type_name in source_table.type_tables:
        # Pass the actual TradeGood objects, not their names
        goods = source_table.type_tables[type_name].goods
        new_table.add_type_table(type_name, goods)
    target_table.add_classification_table(new_code, new_table)
    return new_table


# Load trade goods data from JSON file
_DATA_PATH = Path(__file__).parent.parent.parent / \
    "resources" / "trade_goods_tables.json"
T5RTGTable = RandomTradeGoodsTable.from_json(_DATA_PATH)
