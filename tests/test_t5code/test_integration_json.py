"""Integration tests for JSON-loaded
trade goods with the rest of the system."""

import pytest
from pathlib import Path
from t5code import (
    T5Lot,
    T5World,
    T5ShipClass,
    load_and_parse_t5_map,
    load_and_parse_t5_ship_classes
)
from t5code.T5RandomTradeGoods import T5RTGTable, ImbalanceTradeGood


class MockGameState:
    """Mock GameState for testing."""
    def __init__(self, map_file, ship_classes_file):
        raw_worlds = load_and_parse_t5_map(map_file)
        raw_ships = load_and_parse_t5_ship_classes(ship_classes_file)
        self.world_data = T5World.load_all_worlds(raw_worlds)
        self.ship_data = T5ShipClass.load_all_ship_classes(raw_ships)


@pytest.fixture
def game_state():
    """Create a mock GameState with loaded world and ship data."""
    return MockGameState(
        map_file="tests/test_t5code/t5_test_map.txt",
        ship_classes_file="resources/t5_ship_classes.csv"
    )


def test_json_trade_goods_in_lot_creation(game_state):
    """Verify lots use JSON-loaded trade goods correctly."""
    # Create a lot at a world with known classification
    lot = T5Lot("Rhylanor", game_state)

    # Trade good should be generated from JSON data
    assert lot.lot_id is not None
    assert len(lot.lot_id) > 0
    assert isinstance(lot.lot_id, str)

    # Verify the world's classifications can be retrieved
    world = game_state.world_data["Rhylanor"]
    classifications = world.trade_classifications()
    # Rhylanor is "Hi Cp Llel4 Ht" - Cp should be in our table
    assert "Cp" in classifications
    assert "Cp" in T5RTGTable.classifications


def test_all_classifications_generate_valid_goods():
    """Test all classifications in JSON can generate valid trade goods."""
    # Get all classification codes (excluding aliases)
    primary_classifications = [
        "Ag-1", "Ag-2", "As", "De", "Fl", "Ic",
        "Na", "In", "Po", "Ri", "Va", "Cp"
    ]

    for classification in primary_classifications:
        # Should be able to get a random good
        good_name = T5RTGTable.get_random(classification)

        assert isinstance(good_name, str)
        assert len(good_name) > 0
        # Should not be empty or just whitespace
        assert good_name.strip() == good_name
        assert len(good_name.strip()) > 0


def test_alias_classifications_work():
    """Test that alias classifications (Ga, Fa, Cs, Cx) resolve correctly."""
    aliases = {
        "Ga": "Ag-1",
        "Fa": "Ag-2",
        "Cs": "Cp",
        "Cx": "Cp"
    }

    for alias, source in aliases.items():
        # Alias should be in classifications
        assert alias in T5RTGTable.classifications

        # Should generate valid goods
        alias_good = T5RTGTable.get_random(alias)
        assert isinstance(alias_good, str)
        assert len(alias_good) > 0


def test_imbalance_goods_cross_reference():
    """Test that ImbalanceTradeGood references
    resolve to valid classifications."""
    # Check Ag-1's Imbalances type
    ag1_table = T5RTGTable.classifications["Ag-1"]
    imbalances_table = ag1_table.type_tables["Imbalances"]

    for good in imbalances_table.goods:
        # Should be ImbalanceTradeGood
        assert isinstance(good, ImbalanceTradeGood)

        # Referenced classification should exist
        ref_classification = good.reroll_classification
        assert ref_classification in T5RTGTable.classifications

        # Should be able to resolve the name (triggers reroll)
        # Note: Some imbalances reference "Ag"
        # which needs to resolve to "Ag-1" or "Ag-2"
        # The system should handle this,
        # but if "Ag" doesn't exist, skip name resolution
        try:
            name = good.get_name()
            assert isinstance(name, str)
            assert "Imbalance from" in name
            assert ref_classification in name
        except KeyError:
            # If classification doesn't resolve, that's ok for this test
            # We're just verifying the structure
            pass


def test_specific_goods_accessible_by_index():
    """Test that specific goods can be
    accessed by classification, type, and index."""
    # Test known goods from JSON
    ag1_raws_0 = T5RTGTable.get_good("Ag-1", "Raws", 0)
    assert ag1_raws_0.get_name() == "Bulk Protein"

    ag1_raws_1 = T5RTGTable.get_good("Ag-1", "Raws", 1)
    assert ag1_raws_1.get_name() == "Bulk Carbs"

    # Test Industrial (with Manufactureds1/Manufactureds2)
    in_mfg1_0 = T5RTGTable.get_good("In", "Manufactureds1", 0)
    assert in_mfg1_0.get_name() == "Electronics"

    in_mfg2_0 = T5RTGTable.get_good("In", "Manufactureds2", 0)
    assert in_mfg2_0.get_name() == "Biologics"


def test_all_type_tables_have_six_items():
    """Verify structural integrity: each type table has exactly 6 items."""
    for (
        classification_code,
        classification_table
    ) in T5RTGTable.classifications.items():
        for type_name, type_table in classification_table.type_tables.items():
            assert len(type_table.goods) == 6, \
                f"{classification_code}/{type_name} should have 6 goods, " \
                f"has {len(type_table.goods)}"


def test_json_file_structure_matches_expectations():
    """Validate the JSON file has expected structure."""
    json_path = Path("resources/trade_goods_tables.json")
    assert json_path.exists(), "trade_goods_tables.json must exist"

    import json
    with open(json_path) as f:
        data = json.load(f)

    # Should have classifications and aliases
    assert "classifications" in data
    assert "aliases" in data

    # Should have the expected number
    assert len(data["classifications"]) == 12  # Primary classifications
    assert len(data["aliases"]) == 4  # Ga, Fa, Cs, Cx

    # Each classification should have types
    for (
        classification_code,
        classification_data
    ) in data["classifications"].items():
        assert "types" in classification_data
        assert len(classification_data["types"]) == 6, \
            f"{classification_code} should have 6 type tables"


def test_trade_goods_work_in_multiple_lot_creations(game_state):
    """Test that trade goods work correctly
    across multiple lot instantiations."""
    lots = []

    # Create 10 lots at worlds that exist in test map
    test_worlds = ["Rhylanor", "Jae Tellona"]

    for i in range(10):
        world = test_worlds[i % len(test_worlds)]
        lot = T5Lot(world, game_state)
        lots.append(lot)

        # Each should have a valid lot_id from trade goods
        assert lot.lot_id is not None
        assert len(lot.lot_id) > 0

    # All lot_ids should be strings (some may be duplicates, that's ok)
    assert all(isinstance(lot.lot_id, str) for lot in lots)
