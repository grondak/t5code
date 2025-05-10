import unittest
from T5Code.T5Mail import *
from T5Code.GameState import *
from T5Code.T5World import *


class TestT5Mail(unittest.TestCase):
    """Tests for the T5Mail Class"""

    def test_destination_is_less_important_than_origin(self):
        GameState.world_data = None
        with self.assertRaises(Exception) as context:
            mail = T5Mail("Rhylanor", "Jae Tellona", GameState)
        self.assertTrue(
            "GameState.world_data has not been initialized!" in str(context.exception)
        )
        MAP_FILE = "tests/t5_test_map.txt"
        GameState.world_data = T5World.load_all_worlds(
            GameState.load_and_parse_t5_map(MAP_FILE)
        )
        with self.assertRaises(Exception) as context:
            mail = T5Mail("Jae Tellona", "Rhylanor", GameState)
        self.assertTrue(
            "Destination World must be at least Importance-2 less than origin world"
            in str(context.exception)
        )
        mail = T5Mail("Rhylanor", "Jae Tellona", GameState)
        self.assertTrue(mail.origin_importance >= (mail.destination_importance + 2))
