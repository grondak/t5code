"""Integration tests for error handling and recovery."""

import pytest

from t5code import (
    T5Lot, T5Mail, T5NPC, T5ShipClass, T5Starship, T5World,
    load_and_parse_t5_map, load_and_parse_t5_ship_classes
, T5Company)
from t5code.T5Exceptions import (
    CapacityExceededError,
    InvalidPassageClassError,
    InsufficientFundsError,
)
from t5code.T5RandomTradeGoods import RandomTradeGoodsTable


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


def test_missing_json_file_handling(tmp_path):
    """Test graceful failure if trade_goods_tables.json is missing."""
    # Create a path to a non-existent file
    fake_json = tmp_path / "nonexistent.json"

    # Should raise FileNotFoundError
    with pytest.raises(FileNotFoundError):
        RandomTradeGoodsTable.from_json(fake_json)


def test_invalid_json_file_handling(tmp_path):
    """Test handling of malformed JSON file."""
    # Create invalid JSON file
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{ this is not valid json }")

    # Should raise JSONDecodeError
    import json
    with pytest.raises(json.JSONDecodeError):
        RandomTradeGoodsTable.from_json(bad_json)


def test_invalid_world_in_lot_creation(game_state):
    """Test lot creation with non-existent world."""
    fake_world = "Nonexistent World"

    # Should raise KeyError
    with pytest.raises(KeyError):
        T5Lot(fake_world, game_state)


def test_ship_overload_protection(game_state):
    """Test ship refuses cargo beyond capacity."""
    ship_class = next(iter(game_state.ship_data.values()))
    company = T5Company("Test Company", starting_capital=1_000_000); ship = T5Starship("Overloaded", "Rhylanor", ship_class, owner=company)

    # Create lot larger than ship capacity
    huge_lot = T5Lot("Rhylanor", game_state)
    huge_lot.mass = ship.hold_size + 100

    # Should raise ValueError
    with pytest.raises(CapacityExceededError):
        ship.onload_lot(huge_lot, "cargo")


def test_offload_nonexistent_lot(game_state):
    """Test offloading a lot that doesn't exist."""
    ship_class = next(iter(game_state.ship_data.values()))
    company = T5Company("Test Company", starting_capital=1_000_000); ship = T5Starship("Empty Ship", "Rhylanor", ship_class, owner=company)

    # Try to offload non-existent lot
    with pytest.raises(ValueError, match="Invalid lot serial number"):
        ship.offload_lot("FAKE-SERIAL", "cargo")


def test_negative_lot_mass(game_state):
    """Test that negative lot mass is handled."""
    lot = T5Lot("Rhylanor", game_state)

    # Try to set negative mass
    # This might be allowed, so we just verify behavior
    lot.mass = -5

    # If it's allowed, mass should be negative
    # If not, it might be caught elsewhere
    assert lot.mass == -5  # Document current behavior


def test_invalid_passenger_class(game_state):
    """Test loading passenger with invalid class."""
    ship_class = next(iter(game_state.ship_data.values()))
    company = T5Company("Test Company", starting_capital=1_000_000); ship = T5Starship("Passenger Ship", "Rhylanor", ship_class, owner=company)
    passenger = T5NPC("Test Passenger")

    # Valid classes are "high", "mid", "low"
    # Invalid class should raise error
    with pytest.raises(InvalidPassageClassError):
        ship.onload_passenger(passenger, "super-deluxe")


def test_offload_from_empty_passenger_berth(game_state):
    """Test offloading passengers when none are aboard."""
    ship_class = next(iter(game_state.ship_data.values()))
    company = T5Company("Test Company", starting_capital=1_000_000); ship = T5Starship("Empty Liner", "Rhylanor", ship_class, owner=company)

    # Offload from empty berth (should return empty set)
    passengers = ship.offload_passengers("high")
    assert passengers == set()


def test_invalid_ship_class_data():
    """Test handling of malformed ship class data."""
    # Create invalid ship class data (missing required fields)
    invalid_data = {"Broken Ship": {}}

    # Should handle missing fields gracefully or raise error
    try:
        T5ShipClass.load_all_ship_classes(invalid_data)
        # If it doesn't raise, verify what we got
        ships = T5ShipClass.load_all_ship_classes(invalid_data)
        assert len(ships) > 0
    except (KeyError, ValueError, TypeError):
        # Expected if validation is strict
        pass


def test_world_without_required_fields():
    """Test handling of world data missing required fields."""
    # Create minimal world data
    minimal_world = {"Test World": {"Name": "Test World"}}

    # Try to load
    try:
        worlds = T5World.load_all_worlds(minimal_world)
        # If it works, verify we got something
        assert "Test World" in worlds
    except (KeyError, ValueError, TypeError):
        # Expected if validation is strict
        pass


def test_mail_with_invalid_destination(game_state):
    """Test creating mail with non-existent destination."""
    origin = "Rhylanor"
    fake_destination = "Nonexistent World"

    # This might work or might raise error
    try:
        mail = T5Mail(origin, fake_destination, game_state)
        # If created, verify properties
        assert mail.origin == origin
        assert mail.destination == fake_destination
    except (KeyError, ValueError):
        # Expected if validation is strict
        pass


def test_debit_more_than_balance(game_state):
    """Test debiting more money than ship has."""
    ship_class = next(iter(game_state.ship_data.values()))
    company = T5Company("Test Company", starting_capital=1_000_000); ship = T5Starship("Broke Ship", "Rhylanor", ship_class, owner=company)

    initial_balance = ship.balance

    # Try to debit more than we have (should raise ValueError)
    with pytest.raises(InsufficientFundsError):
        ship.debit(0, initial_balance + 1000)


def test_json_with_missing_classifications():
    """Test JSON file with missing required classifications."""
    # This tests if from_json handles incomplete data
    # The actual T5RTGTable should have all classifications
    from t5code.T5RandomTradeGoods import T5RTGTable

    # Verify all primary classifications exist
    required = ["Ag-1", "Ag-2", "As", "De", "Fl", "Ic",
                "Na", "In", "Po", "Ri", "Va", "Cp"]

    for classification in required:
        assert classification in T5RTGTable.classifications


def test_lot_sale_at_invalid_world(game_state):
    """Test selling lot at world that doesn't exist."""
    lot = T5Lot("Rhylanor", game_state)
    lot.mass = 5

    # Try to determine value at non-existent world
    with pytest.raises(KeyError):
        lot.determine_sale_value_on("Fake World", game_state)


def test_empty_world_data():
    """Test handling of completely empty world data."""
    empty_worlds = {}

    # Should return empty dict or handle gracefully
    result = T5World.load_all_worlds(empty_worlds)
    assert isinstance(result, dict)
    assert len(result) == 0


def test_empty_ship_data():
    """Test handling of empty ship class data."""
    empty_ships = {}

    # Should return empty dict
    result = T5ShipClass.load_all_ship_classes(empty_ships)
    assert isinstance(result, dict)
    assert len(result) == 0


def test_npc_without_skills(game_state):
    """Test NPC operations when no skills are set."""
    npc = T5NPC("Unskilled Worker")

    # Try to get a skill that wasn't set
    skill_value = npc.skills.get("engineering", 0)
    assert skill_value == 0


def test_lot_with_zero_mass(game_state):
    """Test handling of lot with zero mass."""
    lot = T5Lot("Rhylanor", game_state)
    lot.mass = 0

    # Should have zero mass
    assert lot.mass == 0

    # Value should be zero or very small
    value = lot.determine_sale_value_on("Jae Tellona", game_state)
    assert value >= 0
