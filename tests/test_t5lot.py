import pytest
import uuid
from unittest.mock import patch
from T5Code.T5Lot import T5Lot
from T5Code.GameState import *
from T5Code.T5World import T5World

MAP_FILE = "tests/t5_test_map.txt"


def is_guid(string):
    try:
        uuid_obj = uuid.UUID(string, version=4)
        return str(uuid_obj) == string.lower()
    except ValueError:
        return False


def setup_gamestate():
    GameState.world_data = T5World.load_all_worlds(load_and_parse_t5_map(MAP_FILE))


def test_value():
    with pytest.raises(Exception) as excinfo:
        GameState.world_data = None
        lot = T5Lot("Rhylanor", GameState)
    assert "GameState.world_data has not been initialized!" in str(excinfo.value)
    setup_gamestate()
    lot = T5Lot("Rhylanor", GameState)
    assert lot.origin_value == 3500


def test_cargo_id():
    with pytest.raises(Exception) as excinfo:
        GameState.world_data = None
        lot = T5Lot("Rhylanor", GameState)
    assert "GameState.world_data has not been initialized!" in str(excinfo.value)
    setup_gamestate()
    lot = T5Lot("Rhylanor", GameState)
    assert lot.lot_id == "F-Hi 3500"


def test_lot_mass():
    setup_gamestate()
    lot = T5Lot("Rhylanor", GameState)
    assert lot.mass > 0


def test_lot_serial():
    setup_gamestate()
    lot = T5Lot("Rhylanor", GameState)
    assert is_guid(lot.serial)


def test_determine_sale_value_on():
    setup_gamestate()
    lot = T5Lot("Rhylanor", GameState)
    sale_value = lot.determine_sale_value_on("Jae Tellona", GameState)
    assert sale_value == 8500


def test_buying_trade_class_effects():
    test_trade_classifications_table = {
        "Bob": 1000,
        "Doug": -500,
    }
    test_trade_classifications = "Bob Doug"
    value = T5Lot.determine_buying_trade_classifications_effects(
        test_trade_classifications, test_trade_classifications_table
    )
    assert value == 500


def test_selling_trade_class_effect():
    origin_trade_classifications = "In"
    selling_goods_trade_classifications_table = {"In": "Ag In"}
    setup_gamestate()
    marketWorld = GameState.world_data["Jae Tellona"]
    adjustment = T5Lot.determine_selling_trade_classifications_effects(
        marketWorld,
        origin_trade_classifications,
        selling_goods_trade_classifications_table,
    )
    assert adjustment == 1000


def test_lot_costs():
    test_trade_classifications_table = {
        "Bob": 1000,
        "Doug": -500,
    }
    test_trade_classifications = "Bob Doug"
    value = T5Lot.determine_lot_cost(
        test_trade_classifications, test_trade_classifications_table, 5
    )
    assert value == 4000


def test_filter_trade_classifications():
    provided_trade_classifications = ""
    allowed_trade_classifications = ""
    answer = T5Lot.filter_trade_classifications(
        provided_trade_classifications, allowed_trade_classifications
    )
    assert answer == ""
    provided_trade_classifications = "I like kittens"
    allowed_trade_classifications = ""
    answer = T5Lot.filter_trade_classifications(
        provided_trade_classifications, allowed_trade_classifications
    )
    assert answer == ""
    provided_trade_classifications = "I like kittens"
    allowed_trade_classifications = "I like kittens"
    answer = T5Lot.filter_trade_classifications(
        provided_trade_classifications, allowed_trade_classifications
    )
    assert set(answer.split()) == {"I", "like", "kittens"}


def test_equality_and_hash():
    setup_gamestate()
    lot1 = T5Lot("Rhylanor", GameState)
    lot2 = T5Lot("Rhylanor", GameState)
    lot2.serial = lot1.serial
    lot3 = T5Lot("Jae Tellona", GameState)

    # Test __eq__
    assert lot1 == lot2
    assert lot1 != lot3

    # Test __hash__ consistency
    assert hash(lot1) == hash(lot2)
    assert hash(lot1) != hash(lot3)

    # FORCE Coverage to notice this hash function
    lot1.__hash__()

    # Test set behavior
    lot_set = {lot1, lot3}
    assert lot2 in lot_set  # lot2 == lot1
    assert len(lot_set) == 2

    # Test dict behavior
    lot_dict = {lot1: "Freight", lot3: "Cargo"}
    assert lot_dict[lot2] == "Freight"


@pytest.fixture
def lot():
    setup_gamestate()
    return T5Lot("Rhylanor", GameState)


@patch("random.randint")
def test_flux_with_positive_mod(mock_randint, lot):
    mock_randint.side_effect = [6, 1]
    assert lot.consult_actual_value_table(2) == 3.0


@patch("random.randint")
def test_flux_with_negative_mod_below_bounds(mock_randint, lot):
    mock_randint.side_effect = [1, 6]
    assert lot.consult_actual_value_table(-2) == 0.4


@patch("random.randint")
def test_flux_with_zero_mod(mock_randint, lot):
    mock_randint.side_effect = [3, 3]
    assert lot.consult_actual_value_table(0) == 1.0


@patch("random.randint")
def test_flux_middle_case(mock_randint, lot):
    mock_randint.side_effect = [4, 2]
    assert lot.consult_actual_value_table(3) == 1.7


@patch("random.randint")
def test_flux_above_max_bounds(mock_randint, lot):
    mock_randint.side_effect = [6, 2]
    assert lot.consult_actual_value_table(5) == 4.0
