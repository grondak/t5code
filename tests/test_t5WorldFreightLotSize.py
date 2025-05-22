import unittest
from unittest.mock import patch
from T5Code.T5World import T5World


class TestT5WorldFreightLotQuantity(unittest.TestCase):

    def setUp(self):
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

        self.world = DummyWorld()

    @patch("T5Code.T5World.roll_flux", return_value=2)
    def test_freight_size_with_trade_tags(self, mock_flux):
        result = self.world.freight_lot_size(liaison_bonus=3)
        # (2 + 5) * 2 + 3 = 17
        self.assertEqual(result, 17)

    @patch("T5Code.T5World.roll_flux", return_value=2)
    def test_freight_size_without_trade_tags(self, mock_flux):
        self.world.trade_classifications = lambda: ["Hi", "Huh"]
        result = self.world.freight_lot_size(liaison_bonus=1)
        # (2 + 5) * 2 + 1 = 15
        self.assertEqual(result, 15)

    @patch("T5Code.T5World.roll_flux", return_value=-5)
    def test_freight_size_cannot_be_negative(self, mock_flux):
        self.world.trade_classifications = lambda: []
        self.world.get_population = lambda: 2
        result = self.world.freight_lot_size(liaison_bonus=0)
        # (-5 + 2) * 1 + 0 = -3 → should be clipped to 0
        self.assertEqual(result, 0)
