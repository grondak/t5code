import unittest, uuid
from T5Code.T5Lot import T5Lot
from T5Code.GameState import *
from T5Code.T5World import T5World


class TestT5Lot(unittest.TestCase):
    """Tests for the class T5Lot"""

    def is_guid(self, string):
        try:
            uuid_obj = uuid.UUID(
                string, version=4
            )  # Specify the UUID version to validate
            return (
                str(uuid_obj) == string.lower()
            )  # Check normalized form matches input
        except ValueError:
            return False

    def test_value(self):
        with self.assertRaises(Exception) as context:
            GameState.world_data = None
            lot = T5Lot("Rhylanor", GameState)
        self.assertTrue(
            "GameState.world_data has not been initialized!" in str(context.exception)
        )
        MAP_FILE = "tests/t5_test_map.txt"
        GameState.world_data = T5World.load_all_worlds(
            load_and_parse_t5_map(MAP_FILE)
        )
        lot = T5Lot("Rhylanor", GameState)
        self.assertEqual(3500, lot.origin_value)

    def test_cargo_id(self):
        with self.assertRaises(Exception) as context:
            GameState.world_data = None
            lot = T5Lot("Rhylanor", GameState)
        self.assertTrue(
            "GameState.world_data has not been initialized!" in str(context.exception)
        )
        MAP_FILE = "tests/t5_test_map.txt"
        GameState.world_data = T5World.load_all_worlds(
            load_and_parse_t5_map(MAP_FILE)
        )
        lot = T5Lot("Rhylanor", GameState)
        self.assertEqual("F-Hi 3500", lot.lot_id)

    def test_lot_mass(self):
        MAP_FILE = "tests/t5_test_map.txt"
        GameState.world_data = T5World.load_all_worlds(
            load_and_parse_t5_map(MAP_FILE)
        )
        lot = T5Lot("Rhylanor", GameState)
        self.assertGreater(lot.mass, 0)

    def test_lot_serial(self):
        MAP_FILE = "tests/t5_test_map.txt"
        GameState.world_data = T5World.load_all_worlds(
            load_and_parse_t5_map(MAP_FILE)
        )
        lot = T5Lot("Rhylanor", GameState)
        self.assertTrue(self.is_guid(lot.serial))

    def test_determine_sale_value_on(self):
        MAP_FILE = "tests/t5_test_map.txt"
        GameState.world_data = T5World.load_all_worlds(
            load_and_parse_t5_map(MAP_FILE)
        )
        lot = T5Lot("Rhylanor", GameState)
        sale_value = lot.determine_sale_value_on("Jae Tellona", GameState)
        self.assertEqual(8500, sale_value)

    def test_buying_trade_class_effects(self):
        test_trade_classifications_table = {
            "Bob": 1000,
            "Doug": -500,
        }
        test_trade_classifications = "Bob Doug"
        value = T5Lot.determine_buying_trade_classifications_effects(
            test_trade_classifications, test_trade_classifications_table
        )
        self.assertEqual(500, value)

    def test_selling_trade_class_effect(self):
        origin_trade_classifications = "In"
        selling_goods_trade_classifications_table = {"In": "Ag In"}
        MAP_FILE = "tests/t5_test_map.txt"
        GameState.world_data = T5World.load_all_worlds(
            load_and_parse_t5_map(MAP_FILE)
        )
        marketWorld = GameState.world_data["Jae Tellona"]
        adjustment = T5Lot.determine_selling_trade_classifications_effects(
            marketWorld,
            origin_trade_classifications,
            selling_goods_trade_classifications_table,
        )
        self.assertEqual(1000, adjustment)

    def test_lot_costs(self):
        test_trade_classifications_table = {
            "Bob": 1000,
            "Doug": -500,
        }
        test_trade_classifications = "Bob Doug"
        value = T5Lot.determine_lot_cost(
            test_trade_classifications, test_trade_classifications_table, 5
        )
        self.assertEqual(4000, value)

    def test_filter_trade_classifications(self):
        provided_trade_classifications = ""
        allowed_trade_classifications = ""
        answer = T5Lot.filter_trade_classifications(
            provided_trade_classifications, allowed_trade_classifications
        )
        self.assertEqual("", answer)
        provided_trade_classifications = "I like kittens"
        allowed_trade_classifications = ""
        answer = T5Lot.filter_trade_classifications(
            provided_trade_classifications, allowed_trade_classifications
        )
        self.assertEqual("", answer)
        provided_trade_classifications = "I like kittens"
        allowed_trade_classifications = "I like kittens"
        answer = T5Lot.filter_trade_classifications(
            provided_trade_classifications, allowed_trade_classifications
        )
        self.assertEqual({"I", "like", "kittens"}, set(answer.split()))

    def test_equality_and_hash(self):
        MAP_FILE = "tests/t5_test_map.txt"
        GameState.world_data = T5World.load_all_worlds(
            load_and_parse_t5_map(MAP_FILE)
        )
        lot1 = T5Lot("Rhylanor", GameState)
        lot2 = T5Lot("Rhylanor", GameState)
        lot2.serial = lot1.serial
        lot3 = T5Lot("Jae Tellona", GameState)

        # Test __eq__
        self.assertEqual(lot1, lot2)
        self.assertNotEqual(lot1, lot3)

        # Test __hash__ consistency
        self.assertEqual(hash(lot1), hash(lot2))
        self.assertNotEqual(hash(lot1), hash(lot3))
        
        # FORCE Coverage to notice this hash function
        lot1.__hash__()

        # Test set behavior
        lot_set = {lot1, lot3}
        self.assertIn(lot2, lot_set)  # lot2 == lot1
        self.assertEqual(len(lot_set), 2)

        # Test dict behavior
        lot_dict = {lot1: "Freight", lot3: "Cargo"}
        self.assertEqual(lot_dict[lot2], "Freight")


if __name__ == "__main__":
    MAP_FILE = "t5_test_map.txt"
    GameState.world_data = T5World.load_all_worlds(
        load_and_parse_t5_map(MAP_FILE)
    )
    unittest.main()
