import unittest, uuid
from T5Code.T5NPC import *


class TestT5NPC(unittest.TestCase):
    """Tests for the class T5NPC"""

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

    def test_create_NPC_with_name(self):
        npc = T5NPC("Bob")
        self.assertEqual("Bob", npc.characterName)
        self.assertTrue(self.is_guid(npc.serial))
        self.assertEqual(npc.location, None)

    def test_update_location(self):
        npc = T5NPC("Doug")
        self.assertEqual(npc.location, None)
        npc.update_location("A new place")
        self.assertEqual(npc.location, "A new place")

    def test_set_and_get_skill(self):
        npc = T5NPC("Doug")
        self.assertEqual(npc.skills, {})
        npc.set_skill("medic", 5)
        self.assertEqual(npc.get_skill("medic"), 5)

    def test_get_state(self):
        npc = T5NPC("Doug")
        self.assertEqual(npc.get_state(), "Alive")

    def test_kill(self):
        npc = T5NPC("Doug")
        npc.kill()
        self.assertEqual(npc.get_state(), "Dead")
