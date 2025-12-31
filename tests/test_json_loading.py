"""Test JSON loading functionality for T5RandomTradeGoods."""

from pathlib import Path
from t5code.T5RandomTradeGoods import RandomTradeGoodsTable


def test_load_from_json():
    """Test that trade goods can be loaded from JSON file."""
    json_path = Path(__file__).parent.parent / "resources" / \
        "trade_goods_tables.json"

    # Load the table
    table = RandomTradeGoodsTable.from_json(json_path)

    # Verify classifications are loaded
    assert "Ag-1" in table.classifications
    assert "Ag-2" in table.classifications
    assert "As" in table.classifications

    # Verify aliases work
    assert "Ga" in table.classifications
    assert "Fa" in table.classifications

    # Test getting a specific good
    ag1_table = table.classifications["Ag-1"]
    raws_good = ag1_table.get_good("Raws", 0)
    assert raws_good.get_name() == "Bulk Protein"

    # Test random selection works
    random_good = table.get_random("Ag-1")
    assert isinstance(random_good, str)
    assert len(random_good) > 0

    # Test that As imbalances reference Ag (which exists)
    as_table = table.classifications["As"]
    as_imbalance = as_table.get_good("Imbalances", 0)
    # ImbalanceTradeGood references "Ag" which should resolve
    # Note: Getting the name will trigger reroll,
    # which requires "Ag" classification
    # Since "Ag" is not in our sample,
    # we'll just verify it's an ImbalanceTradeGood
    from t5code.T5RandomTradeGoods import ImbalanceTradeGood
    assert isinstance(as_imbalance, ImbalanceTradeGood)
    assert as_imbalance.reroll_classification[0:2] == "Ag"

    # Test alias points to same data structure
    ga_table = table.classifications["Ga"]
    ga_raws_good = ga_table.get_good("Raws", 0)
    assert ga_raws_good.get_name() == "Bulk Protein"


def test_json_structure_validation():
    """Test that JSON structure is correctly validated."""
    json_path = Path(__file__).parent.parent / "resources" / \
        "trade_goods_tables.json"

    table = RandomTradeGoodsTable.from_json(json_path)

    # Each classification should have exactly 6 type tables
    for (
        classification_code,
        classification_table
     ) in table.classifications.items():
        if classification_code not in ["Ga", "Fa"]:  # Aliases
            assert len(classification_table.type_tables) == 6, \
                f"{classification_code} should have 6 type tables"

    # Each type table should have exactly 6 goods
    ag1 = table.classifications["Ag-1"]
    for type_name, type_table in ag1.type_tables.items():
        assert len(type_table.goods) == 6, \
            f"Ag-1/{type_name} should have 6 goods"
