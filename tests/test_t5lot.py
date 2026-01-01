"""Tests for cargo lot representation, pricing, and market mechanics."""

import pytest
import uuid
from unittest.mock import patch
from t5code.T5Lot import T5Lot
from t5code.GameState import load_and_parse_t5_map, GameState
from t5code.T5World import T5World

MAP_FILE = "tests/t5_test_map.txt"


def is_guid(string):
    try:
        uuid_obj = uuid.UUID(string, version=4)
        return str(uuid_obj) == string.lower()
    except ValueError:
        return False


def setup_gamestate():
    GameState.world_data = T5World.load_all_worlds(
        load_and_parse_t5_map(MAP_FILE))


def test_value():
    """Verify lot value is calculated correctly (3500 for Rhylanor)."""
    with pytest.raises(Exception) as excinfo:
        GameState.world_data = None
        T5Lot("Rhylanor", GameState)
    assert "GameState.world_data has not been initialized!" in str(
        excinfo.value)
    setup_gamestate()
    lot = T5Lot("Rhylanor", GameState)
    assert lot.origin_value == 3500


def test_cargo_id():
    """Verify lot ID format includes trade code
    and value (e.g., 'F-Hi 3500')."""
    with pytest.raises(Exception) as excinfo:
        GameState.world_data = None
        T5Lot("Rhylanor", GameState)
    assert "GameState.world_data has not been initialized!" in str(
        excinfo.value)
    setup_gamestate()
    lot = T5Lot("Rhylanor", GameState)
    assert lot.lot_id == "F-Hi 3500"


def test_lot_mass():
    """Verify lot mass is generated as a positive value."""
    setup_gamestate()
    lot = T5Lot("Rhylanor", GameState)
    assert lot.mass > 0


def test_lot_serial():
    """Verify lot serial is a valid UUID."""
    setup_gamestate()
    lot = T5Lot("Rhylanor", GameState)
    assert is_guid(lot.serial)


def test_determine_sale_value_on():
    """Verify sale value is adjusted based on destination world."""
    setup_gamestate()
    lot = T5Lot("Rhylanor", GameState)
    sale_value = lot.determine_sale_value_on("Jae Tellona", GameState)
    assert sale_value == 8500


def test_buying_trade_class_effects():
    """Verify trade classification modifiers
    apply correctly to purchase price."""
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
    """Verify selling market trade classifications affect sale price."""
    origin_trade_classifications = "In"
    selling_goods_trade_classifications_table = {"In": "Ag In"}
    setup_gamestate()
    market_world = GameState.world_data["Jae Tellona"]
    adjustment = T5Lot.determine_selling_trade_classifications_effects(
        market_world,
        origin_trade_classifications,
        selling_goods_trade_classifications_table,
    )
    assert adjustment == 1000


def test_lot_costs():
    """Verify lot cost calculation with trade classification modifiers."""
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
    """Verify filtering of trade classifications by allowed set."""
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
    """Verify lots with same serial are equal and have matching hash values."""
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
    """Verify actual value table lookup with positive modifier."""
    mock_randint.side_effect = [6, 1]
    assert lot.consult_actual_value_table(2) == pytest.approx(3.0)


@patch("random.randint")
def test_flux_with_negative_mod_below_bounds(mock_randint, lot):
    """Verify actual value table clamps minimum to 0.4."""
    mock_randint.side_effect = [1, 6]
    assert lot.consult_actual_value_table(-2) == pytest.approx(0.4)


@patch("random.randint")
def test_flux_with_zero_mod(mock_randint, lot):
    """Verify actual value table lookup with zero modifier."""
    mock_randint.side_effect = [3, 3]
    assert lot.consult_actual_value_table(0) == pytest.approx(1.0)


@patch("random.randint")
def test_flux_middle_case(mock_randint, lot):
    """Verify actual value table lookup for mid-range modifier."""
    mock_randint.side_effect = [4, 2]
    assert lot.consult_actual_value_table(3) == pytest.approx(1.7)


@patch("random.randint")
def test_flux_above_max_bounds(mock_randint, lot):
    """Verify actual value table clamps maximum to 4.0."""
    mock_randint.side_effect = [6, 2]
    assert lot.consult_actual_value_table(5) == pytest.approx(4.0)


def test_predict_actual_value_range_no_modifier(lot):
    """Test predict_actual_value_range with no broker modifier."""
    from t5code.T5Basics import SequentialFlux

    # Pre-roll first die as 4
    flux = SequentialFlux(first_die=4)

    min_val, max_val, returned_flux = lot.predict_actual_value_range(0, flux)

    # With first die=4, flux ranges from -2 (4-6) to +3 (4-1)
    # With mod=0: flux ranges from -2 to +3
    # ACTUAL_VALUE[-2] = 0.8, ACTUAL_VALUE[3] = 1.3
    assert min_val == pytest.approx(0.8)
    assert max_val == pytest.approx(1.3)
    assert returned_flux is flux


def test_predict_actual_value_range_with_positive_modifier(lot):
    """Test predict_actual_value_range with positive broker modifier."""
    from t5code.T5Basics import SequentialFlux

    # Pre-roll first die as 3
    flux = SequentialFlux(first_die=3)

    min_val, max_val, returned_flux = lot.predict_actual_value_range(2, flux)

    # With first die=3, flux ranges from -3 (3-6) to +2 (3-1)
    # With mod=2: flux ranges from -1 to +4
    # ACTUAL_VALUE[-1] = 0.9, ACTUAL_VALUE[4] = 1.5
    assert min_val == pytest.approx(0.9)
    assert max_val == pytest.approx(1.5)
    assert returned_flux is flux


def test_predict_actual_value_range_with_clamping(lot):
    """Test predict_actual_value_range clamps to table bounds."""
    from t5code.T5Basics import SequentialFlux

    # Pre-roll first die as 6 (max)
    flux = SequentialFlux(first_die=6)

    min_val, max_val, returned_flux = lot.predict_actual_value_range(5, flux)

    # With first die=6, flux ranges from 0 (6-6) to +5 (6-1)
    # With mod=5: flux ranges from +5 to +10, but clamped to [+5, +8]
    # ACTUAL_VALUE[5] = 1.7, ACTUAL_VALUE[8] = 4.0 (max)
    assert min_val == pytest.approx(1.7)
    assert max_val == pytest.approx(4.0)
    assert returned_flux is flux


def test_predict_actual_value_range_creates_flux_if_none(lot):
    """Test predict_actual_value_range creates
    SequentialFlux if not provided."""
    with patch("random.randint", return_value=3):
        _, _, flux = lot.predict_actual_value_range(0)

    # Should have created a new SequentialFlux and rolled first die
    from t5code.T5Basics import SequentialFlux
    assert isinstance(flux, SequentialFlux)
    assert flux.first_die == 3
