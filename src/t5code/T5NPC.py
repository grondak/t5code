import uuid
from t5code.T5Tables import SKILLS_BY_GROUP

ALL_KNOWN_SKILLS = {
    skill.lower(): group_name
    for group_name, skills in SKILLS_BY_GROUP.items()
    for skill in skills
}


class T5NPC:
    """An NPC class intended to implement just enough of the T5
    character concepts to function in the simulator"""

    def __init__(self, character_name):
        # Core identity
        self.character_name = character_name
        self.serial = str(uuid.uuid4())  # Unique persistent ID

        # Starting attributes
        self.location = None  # Assigned when placed in a world or ship
        self.skills = {}  # e.g. {"Broker": 2, "Gun Combat": 1}
        self.state = "Alive"  # Could be "Alive", "Missing", "Dead", etc.

    def update_location(self, location):
        self.location = location

    def set_skill(self, name, level):
        key = name.lower()
        if key not in ALL_KNOWN_SKILLS:
            raise ValueError(f"Unknown skill: '{name}'")
        self.skills[key] = level

    def get_skill(self, name):
        return self.skills.get(name.lower(), 0)

    def skill_group(self, name):
        """Optional: Returns the group this skill
        belongs to, or None if unknown."""
        return ALL_KNOWN_SKILLS.get(name.lower())

    def kill(self):
        self.state = "Dead"

    def get_state(self):
        return self.state
