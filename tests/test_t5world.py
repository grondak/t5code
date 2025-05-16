import unittest
from T5Code.T5World import T5World


class TestT5World(unittest.TestCase):
    """Tests for the class T5World"""

    test_world_data = {
        "Earth": {
            "UWP": "A111111-A",
            "TradeClassifications": "Ag As",
            "Importance": 4,
        },
        "Mars": {
            "UWP": "B222222-B",
            "TradeClassifications": "Ba De",
            "Importance": -1,
        },
    }

    def test_UWP(self):
        test_world = T5World("Earth", self.test_world_data)
        self.assertEqual("A111111-A", test_world.UWP())
        with self.assertRaises(Exception) as context:
            test_world = T5World("Bogus", self.test_world_data)
        self.assertTrue(
            "Specified world Bogus is not in provided worlds table"
            in str(context.exception)
        )

    def test_trade_classifications(self):
        test_world = T5World("Earth", self.test_world_data)
        self.assertEqual("Ag As", test_world.trade_classifications())

    def test_importance(self):
        test_world = T5World("Earth", self.test_world_data)
        self.assertEqual(4, test_world.importance())

    def test_load_all_worlds(self):
        test_worlds = T5World.load_all_worlds(self.test_world_data)
        self.assertEqual(2, len(test_worlds))


if __name__ == "__main__":
    unittest.main()
