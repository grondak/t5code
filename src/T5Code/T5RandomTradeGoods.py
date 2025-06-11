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
        "",
        "",
        "",
        "",
        "",
        "",
    ],
)
T5RTGTable.add_classification_table("", blank_table)
"""

ag2_table = TradeClassificationGoodsTable("Ag-2")
ag2_table.add_type_table(
    "Raws",
    [
        "Bulk Woods",
        "Bulk Pelts",
        "Bulk Herbs",
        "Bulk Spices",
        "Bulk Nitrates",
        "Foodstuffs",
    ],
)
ag2_table.add_type_table(
    "Consumables",
    [
        "Flowers",
        "Aromatics",
        "Pheromones",
        "Secretions",
        "Adhesives",
        "Novel Flavorings",
    ],
)
ag2_table.add_type_table(
    "Pharma",
    [
        "Antifungals",
        "Antivirals",
        "Panacea",
        "Pseudomones",
        "Anagathics",
        "Slow Drug",
    ],
)
ag2_table.add_type_table(
    "Novelties",
    [
        "Strange Seeds",
        "Motile Plants",
        "Reactive Plants",
        "Reactive Woods",
        "IR Emitters",
        "Lek Emitters",
    ],
)
ag2_table.add_type_table(
    "Rares",
    [
        "Spices",
        "Organic Gems",
        "Flavorings",
        "Aged Meats",
        "Fermented Fluids",
        "Fine Aromatics",
    ],
)
ag2_table.add_type_table(
    "Imbalances",
    [
        "Po",
        "Ri",
        "Va",
        "Ic",
        "Na",
        "In",
    ],
)
T5RTGTable.add_classification_table("Ag-2", ag2_table)
# Fa entry (same as Ag-2)
clone_classification_table("Fa", ag2_table, T5RTGTable)

as_table = TradeClassificationGoodsTable("As")
as_table.add_type_table(
    "Raws",
    [
        "Bulk Nitrates",
        "Bulk Carbon",
        "Bulk Iron",
        "Bulk Copper",
        "Radioactive Ores",
        "Bulk Ices",
    ],
)
as_table.add_type_table(
    "Samples",
    [
        "Ores",
        "Ices",
        "Carbons",
        "Metals",
        "Uranium",
        "Chelates",
    ],
)
as_table.add_type_table(
    "Valuata",
    [
        "Platinum",
        "Gold",
        "Gallium",
        "Silver",
        "Thorium",
        "Radium",
    ],
)
as_table.add_type_table(
    "Novelties",
    [
        "Unusual Rocks",
        "Fused Metals",
        "Strange Crystals",
        "Fine Dusts",
        "Magnetics",
        "Light-Sensitives",
    ],
)
as_table.add_type_table(
    "Rares",
    [
        "Gemstones",
        "Alloys",
        "Iridium Sponge",
        "Lanthanum",
        "Isotopes",
        "Anti-Matter",
    ],
)
as_table.add_type_table(
    "Imbalances",
    [
        "Ag",
        "De",
        "Na",
        "Po",
        "Ri",
        "Ic",
    ],
)
T5RTGTable.add_classification_table("As", as_table)
de_table = TradeClassificationGoodsTable("De")
de_table.add_type_table(
    "Raws",
    [
        "Bulk Nitrates",
        "Bulk Minerals",
        "Bulk Abrasives",
        "Bulk Particulates",
        "Exotic Fauna",
        "Exotic Flora",
    ],
)
de_table.add_type_table(
    "Samples",
    [
        "Archeologicals",
        "Fauna",
        "Flora",
        "Minerals",
        "Ephemerals",
        "Polymers",
    ],
)
de_table.add_type_table(
    "Pharma",
    [
        "Stimulants",
        "Bulk Herbs",
        "Paliatives",
        "Pheromones",
        "Antibiotics",
        "Combat Drug",
    ],
)
de_table.add_type_table(
    "Novelties",
    [
        "Envirosuits",
        "Reclamation Suits",
        "Navigators",
        "Dupe Masterpieces",
        "ShimmerCloth",
        "ANIFX Blocker",
    ],
)
de_table.add_type_table(
    "Rares",
    [
        "Excretions",
        "Flavorings",
        "Nectars",
        "Pelts",
        "ANIFX Dyes",
        "Seedstock",
    ],
)
de_table.add_type_table(
    "Uniques",
    [
        "Pheromones",
        "Artifacts",
        "Sparx",
        "Repulsant",
        "Dominants",
        "Fossils",
    ],
)
T5RTGTable.add_classification_table("De", de_table)
fl_table = TradeClassificationGoodsTable("Fl")
fl_table.add_type_table(
    "Raws",
    [
        "Bulk Carbon",
        "Bulk Petros",
        "Bulk Precipiates",
        "Exotic Fluids",
        "Organic Polymers",
        "Bulk Synthetics",
    ],
)
fl_table.add_type_table(
    "Samples",
    [
        "Archeologicals",
        "Fauna",
        "Flora",
        "Germanes",
        "Flill",
        "Chelates",
    ],
)
fl_table.add_type_table(
    "Pharma",
    [
        "Antifungals",
        "Antivirals",
        "Paliatives",
        "Counter-prions",
        "Antibiotics",
        "Cold Sleep Pills",
    ],
)
fl_table.add_type_table(
    "Novelties",
    [
        "Silanes",
        "Lek Emitters",
        "Aware Blockers",
        "Soothants",
        "Self-Solving Puzzles",
        "Fluidic Timepieces",
    ],
)
fl_table.add_type_table(
    "Rares",
    [
        "Flavorings",
        "Unusual Fluids",
        "Encapsulants",
        "Insidiants",
        "Corrosives",
        "Exotic Aromatics",
    ],
)
fl_table.add_type_table(
    "Imbalances",
    [
        "In",
        "Ri",
        "Ic",
        "Na",
        "Ag",
        "Po",
    ],
)
T5RTGTable.add_classification_table("Fl", fl_table)
ic_table = TradeClassificationGoodsTable("Ic")
ic_table.add_type_table(
    "Raws",
    [
        "Bulk Ices",
        "Bulk Precipitates",
        "Bulk Ephemerals",
        "Exotic Flora",
        "Bulk Gases",
        "Bulk Oxygen",
    ],
)
ic_table.add_type_table(
    "Samples",
    [
        "Archeologicals",
        "Fauna",
        "Flora",
        "Minerals",
        "Luminescents",
        "Polymers",
    ],
)
ic_table.add_type_table(
    "Pharma",
    [
        "Antifungals",
        "Antivirals",
        "Palliatives",
        "Restoratives",
        "Antibiotics",
        "Antiseptics",
    ],
)
ic_table.add_type_table(
    "Novelties",
    [
        "Heat Pumps",
        "Mag Emitters",
        "Percept Blockers",
        "Silanes",
        "Cold Light Blocks",
        "VHDUS Blocker",
    ],
)
ic_table.add_type_table(
    "Rares",
    [
        "Unusual Ices",
        "Cyro Alloys",
        "Rare Minerals",
        "Unusual Fluids",
        "Cryogems",
        "VHDUS Dyes",
    ],
)
ic_table.add_type_table(
    "Uniques",
    [
        "Fossils",
        "Cyrogems",
        "Vision Suppressant",
        "Fission Suppressant",
        "Wafers",
        "Cold Sleep Pills",
    ],
)
T5RTGTable.add_classification_table("Ic", ic_table)
na_table = TradeClassificationGoodsTable("Na")
na_table.add_type_table(
    "Raws",
    [
        "Bulk Abrasives",
        "Bulk Gases",
        "Bulk Minerals",
        "Bulk Precipitates",
        "Exotic Fauna",
        "Exotic Flora",
    ],
)
na_table.add_type_table(
    "Samples",
    [
        "Archeologicals",
        "Fauna",
        "Flora",
        "Minerals",
        "Ephemerals",
        "Polymers",
    ],
)
na_table.add_type_table(
    "Novelties",
    [
        "Branded Tools",
        "Drinkable Lymphs",
        "Strange Seeds",
        "Pattern Creators",
        "Pigments",
        "Warm Leather",
    ],
)
na_table.add_type_table(
    "Rares",
    [
        "Hummingsand",
        "Masterpieces",
        "Fine Carpets",
        "Isotopes",
        "Pelts",
        "Seedstock",
    ],
)
na_table.add_type_table(
    "Uniques",
    [
        "Masterpieces",
        "Unusual Rocks",
        "Artifacts",
        "Non-Fossil Carca",
        "Replicating Clays",
        "ANIFX Emitter",
    ],
)
na_table.add_type_table(
    "Imbalances",
    [
        "Ag",
        "Ri",
        "In",
        "Ic",
        "De",
        "Fl",
    ],
)
T5RTGTable.add_classification_table("Na", na_table)
in_table = TradeClassificationGoodsTable("In")
in_table.add_type_table(
    "Manufactureds",
    [
        "Electronics",
        "Photonics",
        "Magnetics",
        "Fluidics",
        "Polymers",
        "Gravitics",
    ],
)
in_table.add_type_table(
    "Scrap / Waste",
    [
        "Obsoletes",
        "Used Goods",
        "Reparables",
        "Radioactives",
        "Metals",
        "Sludges",
    ],
)
in_table.add_type_table(
    "Manufactureds",
    [
        "Biologics",
        "Mechanicals",
        "Textiles",
        "Weapons",
        "Armor",
        "Robots",
    ],
)
in_table.add_type_table(
    "Pharma",
    [
        "Nostrums",
        "Restoratives",
        "Palliatives",
        "Chelates",
        "Antidotes",
        "Antitoxins",
    ],
)
in_table.add_type_table(
    "Data",
    [
        "Software",
        "Databases",
        "Expert Systems",
        "Upgrades",
        "Backups",
        "Raw Sensings",
    ],
)
in_table.add_type_table(
    "Consumables",
    [
        "Disposables",
        "Respirators",
        "Filter Masks",
        "Combination",
        "Parts",
        "Improvements",
    ],
)
T5RTGTable.add_classification_table("In", in_table)
po_table = TradeClassificationGoodsTable("Po")
po_table.add_type_table(
    "Raws",
    [
        "Bulk Nutrients",
        "Bulk Fibers",
        "Bulk Organics",
        "Bulk Minerals",
        "Bulk Textiles",
        "Exotic Flora",
    ],
)
po_table.add_type_table(
    "Entertainments",
    [
        "Art",
        "Recordings",
        "Writings",
        "Tactiles",
        "Osmancies",
        "Wafers",
    ],
)
po_table.add_type_table(
    "Novelties",
    [
        "Strange Crystals",
        "Strange Seeds",
        "Pigments",
        "Emotion Lighting",
        "Silanes",
        "Flora",
    ],
)
po_table.add_type_table(
    "Rares",
    [
        "Gemstones",
        "Antiques",
        "Collectibles",
        "Allotropes",
        "Spices",
        "Seedstock",
    ],
)
po_table.add_type_table(
    "Uniques",
    [
        "Masterpieces",
        "Exotic Flora",
        "Antiques",
        "Incomprehensibles",
        "Fossiles",
        "VHDUS Emitter",
    ],
)
po_table.add_type_table(
    "Imbalances",
    [
        "In",
        "Ri",
        "Fl",
        "Ic",
        "Ag",
        "Va",
    ],
)
T5RTGTable.add_classification_table("Po", po_table)
ri_table = TradeClassificationGoodsTable("Ri")
ri_table.add_type_table(
    "Raws",
    [
        "Bulk Foodstuffs",
        "Bulk Protein",
        "Bulk Carbs",
        "Bulk Fats",
        "Exotic Flora",
        "Exotic Fauna",
    ],
)
ri_table.add_type_table(
    "Novelties",
    [
        "Echostones",
        "Self-Defenders",
        "Attractants",
        "Sophont Cuisine",
        "Sophont Hats",
        "Variable Tattoos",
    ],
)
ri_table.add_type_table(
    "Consumables",
    [
        "Branded Foods",
        "Branded Drinks",
        "Branded Clothes",
        "Branded Drinks",
        "Flowers",
        "Music",
    ],
)
ri_table.add_type_table(
    "Rares",
    [
        "Delicacies",
        "Spices",
        "Tisanes",
        "Nectars",
        "Pelts",
        "Variable Tattoos",
    ],
)
ri_table.add_type_table(
    "Uniques",
    [
        "Antique Art",
        "Masterpieces",
        "Artifacts",
        "Fine Art",
        "Meson Barriers",
        "Famous Wafers",
    ],
)
ri_table.add_type_table(
    "Entertainments",
    [
        "Edutainments",
        "Recordings",
        "Writings",
        "Tactiles",
        "Osmancies",
        "Wafers",
    ],
)
T5RTGTable.add_classification_table("Ri", ri_table)
va_table = TradeClassificationGoodsTable("Va")
va_table.add_type_table(
    "Raws",
    [
        "Bulk Dusts",
        "Bulk Minerals",
        "Bulk Metals",
        "Radioactive Ores",
        "Bulk Particulates",
        "Ephemerals",
    ],
)
va_table.add_type_table(
    "Novelties",
    [
        "Branded Vacc Suits",
        "Awareness Pinger",
        "Strange Seeds",
        "Pigments",
        "Unusual Minerals",
        "Exotic Crystals",
    ],
)
va_table.add_type_table(
    "Consumables",
    [
        "Branded Foods",
        "Branded Drinks",
        "Branded Clothes",
        "Flavored Drinks",
        "Flowers",
        "Music",
    ],
)
va_table.add_type_table(
    "Rares",
    [
        "Delicacies",
        "Spices",
        "Tisanes",
        "Nectars",
        "Pelts",
        "Variable Tattoos",
    ],
)
va_table.add_type_table(
    "Samples",
    [
        "Archeologicals",
        "Fauna",
        "Flora",
        "Minerals",
        "Ephemerals",
        "Polymers",
    ],
)
va_table.add_type_table(
    "Scrap / Waste",
    [
        "Obsoletes",
        "Used Goods",
        "Reparables",
        "Plutonium",
        "Metals",
        "Sludges",
    ],
)
T5RTGTable.add_classification_table("Va", va_table)
cp_table = TradeClassificationGoodsTable("Cp")
cp_table.add_type_table(
    "Data",
    [
        "Software",
        "Expert Systems",
        "Databases",
        "Upgrades",
        "Backups",
        "Raw Sensings",
    ],
)
cp_table.add_type_table(
    "Novelties",
    [
        "Incenses",
        "Contemplatives",
        "Cold Welders",
        "Polymer Sheets",
        "Hats",
        "Skin Tones",
    ],
)
cp_table.add_type_table(
    "Consumables",
    [
        "Branded Clothes",
        "Branded Devices",
        "Flavored Drinks",
        "Flavorings",
        "Decorations",
        "Group Symbols",
    ],
)
cp_table.add_type_table(
    "Rares",
    [
        "Monumental Art",
        "Holo Scripture",
        "Collectible Books",
        "Jewelry",
        "Museum Items",
        "Monumental Art",
    ],
)
cp_table.add_type_table(
    "Valuata",
    [
        "Coinage",
        "Currency",
        "Money Cards",
        "Gold",
        "Silver",
        "Platinum",
    ],
)
cp_table.add_type_table(
    "Red Tape",
    [
        "Regulations",
        "Synchronizations",
        "Expert Systems",
        "Educationals",
        "Mandates",
        "Accountings",
    ],
)
T5RTGTable.add_classification_table("Cp", cp_table)

# Cs entry (same as Cp)
clone_classification_table("Cs", cp_table, T5RTGTable)
# Cx entry (same as Cp)
clone_classification_table("Cx", cp_table, T5RTGTable)
