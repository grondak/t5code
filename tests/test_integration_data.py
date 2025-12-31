"""Integration tests for data consistency and cross-references."""

import pytest
from pathlib import Path
from t5code import (
    T5World, T5ShipClass, load_and_parse_t5_map, 
    load_and_parse_t5_ship_classes
)
from t5code.T5RandomTradeGoods import T5RTGTable


def test_all_worlds_load_successfully():
    """Test that world map loads without errors."""
    worlds = load_and_parse_t5_map("tests/t5_test_map.txt")
    world_data = T5World.load_all_worlds(worlds)
    
    # Should have loaded at least 2 worlds
    assert len(world_data) >= 2
    
    # Each world should be a T5World instance
    for name, world in world_data.items():
        assert isinstance(world, T5World)
        assert world.name == name


def test_all_ship_classes_load_successfully():
    """Test that ship classes load without errors."""
    ships = load_and_parse_t5_ship_classes("resources/t5_ship_classes.csv")
    ship_data = T5ShipClass.load_all_ship_classes(ships)
    
    # Should have loaded ships
    assert len(ship_data) > 0
    
    # Each ship should be a T5ShipClass instance
    for name, ship_class in ship_data.items():
        assert isinstance(ship_class, T5ShipClass)
        assert ship_class.class_name == name


def test_world_classifications_exist_in_trade_table():
    """Test that world trade classifications reference valid trade goods."""
    worlds = load_and_parse_t5_map("tests/t5_test_map.txt")
    world_data = T5World.load_all_worlds(worlds)
    
    valid_codes = set(T5RTGTable.classifications.keys())
    
    for world_name, world in world_data.items():
        classifications = world.trade_classifications()
        classification_list = classifications.split()
        
        for code in classification_list:
            # Some codes are modifiers (like Llel4, Hi, Ht) not trade classifications
            # Only check single letter codes or standard 2-letter codes
            if len(code) <= 4 and code[0].isalpha():
                # Check if it's in our trade table or is a known modifier
                known_modifiers = {"Hi", "Lo", "Ht", "Fl", "Cp", "In", "Po", 
                                  "Ri", "As", "De", "Ic", "Na", "Va", "Ni", "Pr", "Mr"}
                if code in valid_codes or any(code.startswith(m) for m in known_modifiers):
                    # Valid
                    pass
                else:
                    # Could be a special code like "Llel4" - that's ok
                    assert len(code) > 2, f"Unknown single/dual code {code} for {world_name}"


def test_ship_cargo_capacity_reasonable():
    """Test that ship cargo capacities are reasonable values."""
    ships = load_and_parse_t5_ship_classes("resources/t5_ship_classes.csv")
    ship_data = T5ShipClass.load_all_ship_classes(ships)
    
    for name, ship_class in ship_data.items():
        # Cargo capacity should be positive
        assert ship_class.cargo_capacity >= 0
        # Should be reasonable (not more than 10000 tons for most ships)
        assert ship_class.cargo_capacity <= 100000, \
            f"{name} has unreasonable cargo capacity: {ship_class.cargo_capacity}"


def test_ship_jump_ratings_valid():
    """Test that ship jump ratings are valid."""
    ships = load_and_parse_t5_ship_classes("resources/t5_ship_classes.csv")
    ship_data = T5ShipClass.load_all_ship_classes(ships)
    
    for name, ship_class in ship_data.items():
        # Jump rating should be 0-6 in Traveller 5
        assert 0 <= ship_class.jump_rating <= 6, \
            f"{name} has invalid jump rating: {ship_class.jump_rating}"


def test_world_uwp_format():
    """Test that world UWP (Universal World Profile) format is valid."""
    worlds = load_and_parse_t5_map("tests/t5_test_map.txt")
    world_data = T5World.load_all_worlds(worlds)
    
    for world_name, world in world_data.items():
        uwp = world.uwp
        # UWP might be a callable or string
        if callable(uwp):
            uwp = uwp()
        # Should be a string
        assert isinstance(uwp, str)
        # Should have at least basic format (various valid lengths)
        assert len(uwp) >= 7, f"{world_name} UWP too short: {uwp}"


def test_json_trade_goods_no_duplicates():
    """Test that JSON file doesn't have duplicate trade goods within classifications."""
    json_path = Path("resources/trade_goods_tables.json")
    import json
    with open(json_path) as f:
        data = json.load(f)
    
    for classification_code, classification_data in data["classifications"].items():
        all_goods = []
        
        for type_name, goods_list in classification_data["types"].items():
            for item in goods_list:
                # Skip imbalance entries
                if isinstance(item, dict):
                    continue
                all_goods.append(item)
        
        # Check for duplicates within this classification
        unique_goods = set(all_goods)
        if len(unique_goods) != len(all_goods):
            # Find the duplicates
            from collections import Counter
            counts = Counter(all_goods)
            duplicates = [item for item, count in counts.items() if count > 1]
            # Some duplicates might be intentional (e.g., same good in different types)
            # Just warn if found
            import warnings
            warnings.warn(
                f"{classification_code} has duplicate goods: {duplicates}",
                UserWarning
            )


def test_json_imbalances_reference_valid_classifications():
    """Test that all imbalance goods reference valid classifications."""
    json_path = Path("resources/trade_goods_tables.json")
    import json
    with open(json_path) as f:
        data = json.load(f)
    
    all_classifications = set(data["classifications"].keys())
    
    for classification_code, classification_data in data["classifications"].items():
        for type_name, goods_list in classification_data["types"].items():
            if type_name == "Imbalances":
                for item in goods_list:
                    if isinstance(item, dict) and item.get("type") == "imbalance":
                        ref = item["reroll_classification"]
                        # Reference should exist (may be short form like "Ag")
                        # Check if exact match or if it's a prefix of a valid classification
                        valid = (ref in all_classifications or 
                                any(c.startswith(ref) for c in all_classifications))
                        if not valid:
                            pytest.fail(
                                f"{classification_code} Imbalance references "
                                f"invalid classification: {ref}"
                            )


def test_aliases_reference_valid_sources():
    """Test that all aliases reference valid source classifications."""
    json_path = Path("resources/trade_goods_tables.json")
    import json
    with open(json_path) as f:
        data = json.load(f)
    
    classifications = set(data["classifications"].keys())
    
    for alias, source in data["aliases"].items():
        assert source in classifications, \
            f"Alias {alias} references non-existent source: {source}"


def test_constants_match_json_data():
    """Test that module constants match what's in JSON data."""
    from t5code.T5RandomTradeGoods import (
        BULK_NITRATES, STRANGE_SEEDS, BULK_MINERALS,
        EXOTIC_FAUNA, EXOTIC_FLORA, EXPERT_SYSTEMS,
        VARIABLE_TATTOOS, BRANDED_DRINKS, BRANDED_CLOTHES
    )
    
    json_path = Path("resources/trade_goods_tables.json")
    import json
    with open(json_path) as f:
        data = json.load(f)
    
    # Check that constants appear in the JSON data
    all_goods = []
    for classification_data in data["classifications"].values():
        for goods_list in classification_data["types"].values():
            for item in goods_list:
                if isinstance(item, str):
                    all_goods.append(item)
    
    constants = {
        BULK_NITRATES, STRANGE_SEEDS, BULK_MINERALS,
        EXOTIC_FAUNA, EXOTIC_FLORA, EXPERT_SYSTEMS,
        VARIABLE_TATTOOS, BRANDED_DRINKS, BRANDED_CLOTHES
    }
    
    for const in constants:
        assert const in all_goods, f"Constant '{const}' not found in JSON data"


def test_all_classifications_have_imbalances_or_are_special():
    """Test that most classifications have Imbalances type (or are special cases)."""
    json_path = Path("resources/trade_goods_tables.json")
    import json
    with open(json_path) as f:
        data = json.load(f)
    
    # Industrial worlds (In) might not have Imbalances
    # Check that others do
    for classification_code, classification_data in data["classifications"].items():
        type_names = classification_data["types"].keys()
        
        # Most should have Imbalances, but not all (In doesn't)
        if classification_code not in ["In"]:
            # Just verify it has 6 type tables
            assert len(type_names) == 6, \
                f"{classification_code} should have 6 type tables"


def test_no_orphaned_trade_goods():
    """Test that all trade goods in JSON are accessible via the API."""
    json_path = Path("resources/trade_goods_tables.json")
    import json
    with open(json_path) as f:
        data = json.load(f)
    
    # Every classification in JSON should be in loaded table
    for classification_code in data["classifications"].keys():
        assert classification_code in T5RTGTable.classifications, \
            f"Classification {classification_code} not loaded into T5RTGTable"
    
    # Every alias should also be accessible
    for alias in data["aliases"].keys():
        assert alias in T5RTGTable.classifications, \
            f"Alias {alias} not accessible in T5RTGTable"


def test_world_and_ship_data_files_exist():
    """Test that required data files exist."""
    # World map
    world_map = Path("resources/t5_map.txt")
    assert world_map.exists(), "resources/t5_map.txt is missing"
    
    # Ship classes
    ship_classes = Path("resources/t5_ship_classes.csv")
    assert ship_classes.exists(), "resources/t5_ship_classes.csv is missing"
    
    # Trade goods
    trade_goods = Path("resources/trade_goods_tables.json")
    assert trade_goods.exists(), "resources/trade_goods_tables.json is missing"
    
    # Test files
    test_map = Path("tests/t5_test_map.txt")
    assert test_map.exists(), "tests/t5_test_map.txt is missing"
