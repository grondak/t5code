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
    def __init__(self, name: Union[str, Callable[[], str]]):
        self._name = name

    def get_name(self) -> str:
        return self._name() if callable(self._name) else self._name


class ImbalanceTradeGood(TradeGood):
    def __init__(self, reroll_classification: str,
                 rtg_table: "RandomTradeGoodsTable"):
        self.reroll_classification = reroll_classification
        self.rtg_table = rtg_table
        super().__init__(self.resolve_name)

    def resolve_name(self) -> str:
        rerolled = self.rtg_table.get_random(self.reroll_classification)
        return f"Imbalance from {self.reroll_classification}: " \
            f"{rerolled} (+Cr1,000 if sold on {self.reroll_classification})"


class TradeGoodsTypeTable:
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
        return self.goods[index]

    def roll(self) -> TradeGood:
        return self.get_good(random.randint(DICE_MIN, DICE_MAX))


class TradeClassificationGoodsTable:

    def __init__(self, classification_code: str):
        self.classification_code = classification_code
        self.type_tables: Dict[str, TradeGoodsTypeTable] = {}
        self.type_order: List[str] = []

    def add_type_table(
        self,
        type_name: str,
        goods: Sequence[Union[str, Callable[[], str], "TradeGood"]]
    ):
        if len(self.type_order) >= TABLE_SIZE:
            raise ValueError(
                f"Each classification may only "
                f"have {TABLE_SIZE} TradeGoodsTypeTables."
            )
        self.type_tables[type_name] = TradeGoodsTypeTable(type_name, goods)
        self.type_order.append(type_name)

    def get_good(self, type_name: str, index: int) -> TradeGood:
        return self.type_tables[type_name].get_good(index)

    def roll(self) -> TradeGood:
        type_index = random.randint(DICE_MIN, DICE_MAX)
        type_name = self.type_order[type_index]
        return self.type_tables[type_name].roll()


class RandomTradeGoodsTable:
    def __init__(self):
        self.classifications: Dict[str, TradeClassificationGoodsTable] = {}

    def add_classification_table(
        self, classification_code: str, table: TradeClassificationGoodsTable
    ):
        self.classifications[classification_code] = table

    def get_good(self,
                 classification: str,
                 type_name: str,
                 index: int) -> TradeGood:
        return self.classifications[classification].get_good(type_name, index)

    def get_random(self, classification: str) -> str:
        return self.classifications[classification].roll().get_name()

    @classmethod
    def from_json(cls, json_path: Path) -> "RandomTradeGoodsTable":
        """
        Load trade goods tables from a JSON file.

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
    """
    Clone all type tables from source_table into
    a new TradeClassificationGoodsTable
    with code new_code, and register it in target_table.
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
