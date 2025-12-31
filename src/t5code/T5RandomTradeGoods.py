"""Random trade goods generation for Traveller 5 cargo generation.

Provides tables and logic for generating random trade goods with pricing,
common classifications, and market dynamics.
"""

from typing import Union, Callable, List, Dict
import random

BULK_NITRATES = "Bulk Nitrates"
STRANGE_SEEDS = "Strange Seeds"
BULK_MINERALS = "Bulk Minerals"
EXOTIC_FAUNA = "Exotic Fauna"
EXOTIC_FLORA = "Exotic Flora"
EXPERT_SYSTEMS = "Expert Systems"
VARIABLE_TATTOOS = "Variable Tattoos"
BRANDED_DRINKS = "Branded Drinks"
BRANDED_CLOTHES = "Branded Clothes"


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
                 goods: List[Union[str, Callable[[], str], "TradeGood"]]):
        if len(goods) != 6:
            raise ValueError(f"{type_name} table must have "
                             "exactly 6 trade goods.")
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
        return self.get_good(random.randint(0, 5))


class TradeClassificationGoodsTable:

    def __init__(self, classification_code: str):
        self.classification_code = classification_code
        self.type_tables: Dict[str, TradeGoodsTypeTable] = {}
        self.type_order: List[str] = []

    def add_type_table(
        self,
        type_name: str,
        goods: List[Union[str, Callable[[], str], "TradeGood"]]
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

    def get_good(self,
                 classification: str,
                 type_name: str,
                 index: int) -> TradeGood:
        return self.classifications[classification].get_good(type_name, index)

    def get_random(self, classification: str) -> str:
        return self.classifications[classification].roll().get_name()


def clone_classification_table(new_code, source_table, target_table):
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
ag1_table.add_type_table(
    "Imbalances",
    [
        ImbalanceTradeGood("As", T5RTGTable),
        ImbalanceTradeGood("De", T5RTGTable),
        ImbalanceTradeGood("Fl", T5RTGTable),
        ImbalanceTradeGood("Ic", T5RTGTable),
        ImbalanceTradeGood("Na", T5RTGTable),
        ImbalanceTradeGood("In", T5RTGTable),
    ],
)

T5RTGTable.add_classification_table("Ag-1", ag1_table)


# Ga entry (same as Ag-1)
clone_classification_table("Ga", ag1_table, T5RTGTable)

ag2_table = TradeClassificationGoodsTable("Ag-2")
ag2_table.add_type_table(
    "Raws",
    [
        "Bulk Woods",
        "Bulk Pelts",
        "Bulk Herbs",
        "Bulk Spices",
        BULK_NITRATES,
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
        STRANGE_SEEDS,
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
        ImbalanceTradeGood("Po", T5RTGTable),
        ImbalanceTradeGood("Ri", T5RTGTable),
        ImbalanceTradeGood("Va", T5RTGTable),
        ImbalanceTradeGood("Ic", T5RTGTable),
        ImbalanceTradeGood("Na", T5RTGTable),
        ImbalanceTradeGood("In", T5RTGTable),
    ],
)
T5RTGTable.add_classification_table("Ag-2", ag2_table)
# Fa entry (same as Ag-2)
clone_classification_table("Fa", ag2_table, T5RTGTable)

as_table = TradeClassificationGoodsTable("As")
as_table.add_type_table(
    "Raws",
    [
        BULK_NITRATES,
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
        ImbalanceTradeGood("Ag", T5RTGTable),
        ImbalanceTradeGood("De", T5RTGTable),
        ImbalanceTradeGood("Na", T5RTGTable),
        ImbalanceTradeGood("Po", T5RTGTable),
        ImbalanceTradeGood("Ri", T5RTGTable),
        ImbalanceTradeGood("Ic", T5RTGTable),
    ],
)
T5RTGTable.add_classification_table("As", as_table)
de_table = TradeClassificationGoodsTable("De")
de_table.add_type_table(
    "Raws",
    [
        BULK_NITRATES,
        BULK_MINERALS,
        "Bulk Abrasives",
        "Bulk Particulates",
        EXOTIC_FAUNA,
        EXOTIC_FLORA,
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
        ImbalanceTradeGood("In", T5RTGTable),
        ImbalanceTradeGood("Ri", T5RTGTable),
        ImbalanceTradeGood("Ic", T5RTGTable),
        ImbalanceTradeGood("Na", T5RTGTable),
        ImbalanceTradeGood("Ag", T5RTGTable),
        ImbalanceTradeGood("Po", T5RTGTable),
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
        EXOTIC_FLORA,
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
        BULK_MINERALS,
        "Bulk Precipitates",
        EXOTIC_FAUNA,
        EXOTIC_FLORA,
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
        STRANGE_SEEDS,
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
        ImbalanceTradeGood("Ag", T5RTGTable),
        ImbalanceTradeGood("Ri", T5RTGTable),
        ImbalanceTradeGood("In", T5RTGTable),
        ImbalanceTradeGood("Ic", T5RTGTable),
        ImbalanceTradeGood("De", T5RTGTable),
        ImbalanceTradeGood("Fl", T5RTGTable),
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
        EXPERT_SYSTEMS,
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
        BULK_MINERALS,
        "Bulk Textiles",
        EXOTIC_FLORA,
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
        STRANGE_SEEDS,
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
        EXOTIC_FLORA,
        "Antiques",
        "Incomprehensibles",
        "Fossiles",
        "VHDUS Emitter",
    ],
)
po_table.add_type_table(
    "Imbalances",
    [
        ImbalanceTradeGood("In", T5RTGTable),
        ImbalanceTradeGood("Ri", T5RTGTable),
        ImbalanceTradeGood("Fl", T5RTGTable),
        ImbalanceTradeGood("Ic", T5RTGTable),
        ImbalanceTradeGood("Ag", T5RTGTable),
        ImbalanceTradeGood("Va", T5RTGTable),
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
        EXOTIC_FLORA,
        EXOTIC_FAUNA,
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
        VARIABLE_TATTOOS,
    ],
)
ri_table.add_type_table(
    "Consumables",
    [
        "Branded Foods",
        BRANDED_DRINKS,
        BRANDED_CLOTHES,
        BRANDED_DRINKS,
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
        VARIABLE_TATTOOS,
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
        BULK_MINERALS,
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
        STRANGE_SEEDS,
        "Pigments",
        "Unusual Minerals",
        "Exotic Crystals",
    ],
)
va_table.add_type_table(
    "Consumables",
    [
        "Branded Foods",
        BRANDED_DRINKS,
        BRANDED_CLOTHES,
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
        VARIABLE_TATTOOS,
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
        EXPERT_SYSTEMS,
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
        BRANDED_CLOTHES,
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
        EXPERT_SYSTEMS,
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
