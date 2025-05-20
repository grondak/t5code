import unittest
from T5Code.T5World import T5World, find_best_broker


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

    def test_get_starport_type(self):
        test_world = T5World("Earth", self.test_world_data)
        self.assertEqual("A", test_world.get_starport())

    def test_tier_A(self):
        result = find_best_broker("A")
        self.assertEqual(result, {"name": "Broker-7+", "mod": 4, "rate": 0.2})

    def test_tier_B(self):
        result = find_best_broker("B")
        self.assertEqual(result, {"name": "Broker-6", "mod": 3, "rate": 0.15})

    def test_tier_C(self):
        result = find_best_broker("C")
        self.assertEqual(result, {"name": "Broker-4", "mod": 2, "rate": 0.1})

    def test_tier_D(self):
        result = find_best_broker("D")
        self.assertEqual(result, {"name": "Broker-2", "mod": 1, "rate": 0.05})

    def test_invalid_tier(self):
        with self.assertRaises(ValueError):
            find_best_broker("E")


if __name__ == "__main__":
    unittest.main()
