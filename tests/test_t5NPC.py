import pytest
import uuid
from T5Code.T5NPC import T5NPC


def is_guid(string):
    try:
        uuid_obj = uuid.UUID(string, version=4)
        return str(uuid_obj) == string.lower()
    except ValueError:
        return False


def test_create_NPC_with_name():
    npc = T5NPC("Bob")
    assert npc.characterName == "Bob"
    assert is_guid(npc.serial)
    assert npc.location is None


def test_update_location():
    npc = T5NPC("Doug")
    assert npc.location is None
    npc.update_location("A new place")
    assert npc.location == "A new place"


def test_set_and_get_skill():
    npc = T5NPC("Doug")
    assert npc.skills == {}
    npc.set_skill("medic", 5)
    assert npc.get_skill("medic") == 5
    assert npc.get_skill("pilot") == 0  # assuming 0 default for unset skills
    npc.set_skill("medic", 7)
    assert npc.get_skill("medic") == 7


def test_set_invalid_skill():
    npc = T5NPC("Glorb")
    with pytest.raises(ValueError):
        npc.set_skill("moonwalking", 2)


@pytest.fixture
def npc():
    return T5NPC("TestSubject")


def test_skill_group_known_skill(npc):
    assert npc.skill_group("Medic") == "STARSHIP_SKILLS"
    assert npc.skill_group("Photonics") == "TRADES"
    assert npc.skill_group("Actor") == "ARTS"
    assert npc.skill_group("Command") == "PERSONALS"


def test_skill_group_case_insensitive(npc):
    assert npc.skill_group("mEdIc") == "STARSHIP_SKILLS"
    assert npc.skill_group("gAmBlEr") == "SKILLS"


def test_skill_group_unknown_skill(npc):
    assert npc.skill_group("moonwalking") is None
    assert npc.skill_group("plasma_nunchucks") is None


def test_get_state():
    npc = T5NPC("Doug")
    assert npc.get_state() == "Alive"


def test_kill():
    npc = T5NPC("Doug")
    npc.kill()
    assert npc.get_state() == "Dead"
