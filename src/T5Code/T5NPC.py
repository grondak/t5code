import uuid


class T5NPC:
    """An NPC class intended to implement just enough of the T5 character concepts to function in the simulator"""

    def __init__(self, character_name):
        # Core identity
        self.characterName = character_name
        self.serial = str(uuid.uuid4())  # Unique persistent ID

        # Starting attributes
        self.location = None  # Assigned when placed in a world or ship
        self.skills = {}  # e.g. {"Broker": 2, "Gun Combat": 1}
        self.state = "Alive"  # Could be "Alive", "Missing", "Dead", etc.

    def update_location(self, location):
        self.location = location

    def set_skill(self, skill, value):
        self.skills[skill] = value

    def get_skill(self, skill):
        return self.skills.get(skill, 0)

    def kill(self):
        self.state = "Dead"

    def get_state(self):
        return self.state
