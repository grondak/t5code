from typing import Union, Callable, List, Dict
import random


class TradeGood:
    def __init__(self, name: Union[str, Callable[[], str]]):
        self._name = name

    def get_name(self) -> str:
        return self._name() if callable(self._name) else self._name


class TradeGoodsTypeTable:
    def __init__(self, type_name: str, goods: List[Union[str, Callable[[], str]]]):
        if len(goods) != 6:
            raise ValueError(f"{type_name} table must have exactly 6 trade goods.")
        self.type_name = type_name
        self.goods = [TradeGood(g) for g in goods]

    def get_good(self, index: int) -> TradeGood:
        return self.goods[index]

    def roll(self) -> TradeGood:
        return self.get_good(random.randint(0, 5))


class TradeClassificationGoodsTable:
    def __init__(self, classification_code: str):
        self.classification_code = classification_code
        self.type_tables: Dict[str, TradeGoodsTypeTable] = {}
        self.type_order: List[str] = []

    def add_type_table(
        self, type_name: str, goods: List[Union[str, Callable[[], str]]]
    ):
        if len(self.type_order) >= 6:
            raise ValueError(
                "Each classification may only have 6 TradeGoodsTypeTables."
            )
        self.type_tables[type_name] = TradeGoodsTypeTable(type_name, goods)
        self.type_order.append(type_name)

    def get_good(self, type_name: str, index: int) -> TradeGood:
        return self.type_tables[type_name].get_good(index)

    def roll(self) -> TradeGood:
        type_index = random.randint(0, 5)
        type_name = self.type_order[type_index]
        return self.type_tables[type_name].roll()


class RandomTradeGoodsTable:
    def __init__(self):
        self.classifications: Dict[str, TradeClassificationGoodsTable] = {}

    def add_classification_table(
        self, classification_code: str, table: TradeClassificationGoodsTable
    ):
        self.classifications[classification_code] = table

    def get_good(self, classification: str, type_name: str, index: int) -> TradeGood:
        return self.classifications[classification].get_good(type_name, index)

    def get_random(self, classification: str) -> str:
        return self.classifications[classification].roll().get_name()


def clone_classification_table(new_code, source_table, target_table):
    """
    Clone all type tables from source_table into a new TradeClassificationGoodsTable
    with code new_code, and register it in target_table.
    """
    new_table = TradeClassificationGoodsTable(new_code)
    for type_name in source_table.type_tables:
        goods = [g.get_name() for g in source_table.type_tables[type_name].goods]
        new_table.add_type_table(type_name, goods)
    target_table.add_classification_table(new_code, new_table)
    return new_table


# Data instantiation
T5RTGTable = RandomTradeGoodsTable()

# Ag-1 / Ga entry
ag1_table = TradeClassificationGoodsTable("Ag-1")

ag1_table.add_type_table(
    "Raws",
    [
        "Bulk Protein",
        "Bulk Carbs",
        "Bulk Fats",
        "Bulk Pharma",
        "Livestock",
        "Seedstock",
    ],
)
ag1_table.add_type_table(
    "Consumables",
    [
        "Flavored Waters",
        "Wines",
        "Juices",
        "Nectars",
        "Deconcoctions",
        "Drinkable Lymphs",
    ],
)
ag1_table.add_type_table(
    "Pharma",
    [
        "Health Foods",
        "Nutraceuticals",
        "Fast Drug",
        "Painkillers",
        "Antiseptic",
        "Antibiotics",
    ],
)
ag1_table.add_type_table(
    "Novelties",
    [
        "Incenses",
        "Iridescents",
        "Photonics",
        "Pigments",
        "Noisemakers",
        "Soundmakers",
    ],
)
ag1_table.add_type_table(
    "Rares",
    [
        "Fine Furs",
        "Meat Delicacies",
        "Fruit Delicacies",
        "Candies",
        "Textiles",
        "Exotic Sauces",
    ],
)
ag1_table.add_type_table("Imbalances", ["As", "De", "Fl", "Ic", "Na", "In"])

T5RTGTable.add_classification_table("Ag-1", ag1_table)


# Ga entry (same as Ag-1)
clone_classification_table("Ga", ag1_table, T5RTGTable)


""" 
blank_table = TradeClassificationGoodsTable("Blank")
blank_table.add_type_table(
    "Somethings",
    [
        "" "",
        "",
        "",
        "",
        "",
    ],
)
"""

ag2_table = TradeClassificationGoodsTable("Ag-2")
T5RTGTable.add_classification_table("Ag-2", ag2_table)
# Fa entry (same as Ag-2)
clone_classification_table("Fa", ag2_table, T5RTGTable)

as_table = TradeClassificationGoodsTable("As")
T5RTGTable.add_classification_table("As", as_table)
de_table = TradeClassificationGoodsTable("De")
T5RTGTable.add_classification_table("De", de_table)
fl_table = TradeClassificationGoodsTable("Fl")
T5RTGTable.add_classification_table("Fl", fl_table)
ic_table = TradeClassificationGoodsTable("Ic")
T5RTGTable.add_classification_table("Ic", ic_table)
na_table = TradeClassificationGoodsTable("Na")
T5RTGTable.add_classification_table("Na", na_table)
in_table = TradeClassificationGoodsTable("In")
T5RTGTable.add_classification_table("In", in_table)
po_table = TradeClassificationGoodsTable("Po")
T5RTGTable.add_classification_table("Po", po_table)
ri_table = TradeClassificationGoodsTable("Ri")
T5RTGTable.add_classification_table("Ri", ri_table)
va_table = TradeClassificationGoodsTable("Va")
T5RTGTable.add_classification_table("Va", va_table)
cp_table = TradeClassificationGoodsTable("Cp")
T5RTGTable.add_classification_table("Cp", cp_table)

# Cs entry (same as Cp)
clone_classification_table("Cs", cp_table, T5RTGTable)
# Cx entry (same as Cp)
clone_classification_table("Cx", cp_table, T5RTGTable)
