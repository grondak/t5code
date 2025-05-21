import unittest, uuid
from T5Code.T5NPC import T5NPC


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

        # Ensure starting skillset is empty
        self.assertEqual(npc.skills, {})

        # Set a skill and verify it's stored correctly
        npc.set_skill("medic", 5)
        self.assertEqual(npc.get_skill("medic"), 5)

        # Try getting a skill that hasn't been set
        self.assertEqual(
            npc.get_skill("pilot"), 0
        )  # assuming 0 default for unset skills

        # Overwrite an existing skill
        npc.set_skill("medic", 7)
        self.assertEqual(npc.get_skill("medic"), 7)

    def test_set_invalid_skill(self):
        npc = T5NPC("Glorb")
        with self.assertRaises(ValueError):
            npc.set_skill("moonwalking", 2)

    def setUp(self):
        self.npc = T5NPC("TestSubject")

    def test_skill_group_known_skill(self):
        # Pick a few known skills from various groups
        self.assertEqual(self.npc.skill_group("Medic"), "STARSHIP_SKILLS")
        self.assertEqual(self.npc.skill_group("Photonics"), "TRADES")
        self.assertEqual(self.npc.skill_group("Actor"), "ARTS")
        self.assertEqual(self.npc.skill_group("Command"), "PERSONALS")

    def test_skill_group_case_insensitive(self):
        self.assertEqual(self.npc.skill_group("mEdIc"), "STARSHIP_SKILLS")
        self.assertEqual(self.npc.skill_group("gAmBlEr"), "SKILLS")

    def test_skill_group_unknown_skill(self):
        self.assertIsNone(self.npc.skill_group("moonwalking"))
        self.assertIsNone(self.npc.skill_group("plasma_nunchucks"))

    def test_get_state(self):
        npc = T5NPC("Doug")
        self.assertEqual(npc.get_state(), "Alive")

    def test_kill(self):
        npc = T5NPC("Doug")
        npc.kill()
        self.assertEqual(npc.get_state(), "Dead")
