import unittest
from T5Code.T5ShipClass import T5ShipClass


class TestT5ShipClass(unittest.TestCase):
    """Tests for the T5ShipClass Class"""

    test_ship_data = {
        "small": {
            "class_name": "small",
            "jump_rating": 1,
            "maneuver_rating": 2,
            "cargo_capacity": 10,
        },
        "large": {
            "class_name": "large",
            "jump_rating": 3,
            "maneuver_rating": 3,
            "cargo_capacity": 200,
        },
    }

    def test_USP(self):
        test_class = T5ShipClass("small", self.test_ship_data["small"])
        self.assertEqual("small 12\nCargo: 10 tons", test_class.USP())
        test_class2 = T5ShipClass("large", self.test_ship_data["large"])
        self.assertEqual("large 33\nCargo: 200 tons", test_class2.USP())

    def test_load_all_ship_classes(self):
        test_classes = T5ShipClass.load_all_ship_classes(self.test_ship_data)
        self.assertEqual(len(test_classes), 2)


if __name__ == "__main__":
    unittest.main()
