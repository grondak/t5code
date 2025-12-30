import pytest
from unittest.mock import patch
from t5code.T5World import T5World


class DummyWorld:
    def get_population(self):
        return 5

    def trade_classifications(self):
        return ["In", "Ni"]

    def freight_lot_size(self, liaison_bonus):
        return T5World.freight_lot_mass(self, liaison_bonus)

    TRADE_CODE_MULTIPLIER_TAGS = {
        "Ag",
        "As",
        "Ba",
        "De",
        "Fl",
        "Hi",
        "Ic",
        "In",
        "Lo",
        "Na",
        "Ni",
        "Po",
        "Ri",
        "Va",
    }


@pytest.fixture
def world():
    return DummyWorld()


@patch("t5code.T5World.roll_flux", return_value=2)
def test_freight_size_with_trade_tags(mock_flux, world):
    result = world.freight_lot_size(liaison_bonus=3)
    assert result == 17


@patch("t5code.T5World.roll_flux", return_value=2)
def test_freight_size_without_trade_tags(mock_flux, world):
    world.trade_classifications = lambda: ["Hi", "Huh"]
    result = world.freight_lot_size(liaison_bonus=1)
    assert result == 15


@patch("t5code.T5World.roll_flux", return_value=-5)
def test_freight_size_cannot_be_negative(mock_flux, world):
    world.trade_classifications = lambda: []
    world.get_population = lambda: 2
    result = world.freight_lot_size(liaison_bonus=0)
    # (-5 + 2) * 1 + 0 = -3 → should be clipped to 0
    assert result == 0
