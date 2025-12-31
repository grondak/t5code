"""Non-player character (NPC) representation for Traveller 5.

Defines the T5NPC class for creating and managing NPCs with skills,
used for crew and passenger roles aboard starships.
"""

import uuid
from typing import Dict, Optional
from t5code.T5Tables import SKILLS_BY_GROUP

ALL_KNOWN_SKILLS = {
    skill.lower(): group_name
    for group_name, skills in SKILLS_BY_GROUP.items()
    for skill in skills
}


class T5NPC:
    """An NPC class intended to implement just enough of the T5
    character concepts to function in the simulator"""

    def __init__(self, character_name: str) -> None:
        # Core identity
        self.character_name: str = character_name
        self.serial: str = str(uuid.uuid4())  # Unique persistent ID

        # Starting attributes
        self.location: str = "Unknown"  # Assigned when first decided
        self.skills: Dict[str, int] = {}  # e.g. {"broker": 2, "gun combat": 1}
        self.state: str = "Alive"  # Could be "Alive", "Missing", "Dead", etc.

    def update_location(self, location: str) -> None:
        self.location = location

    def set_skill(self, name: str, level: int) -> None:
        key = name.lower()
        if key not in ALL_KNOWN_SKILLS:
            raise ValueError(f"Unknown skill: '{name}'")
        self.skills[key] = level

    def get_skill(self, name: str) -> int:
        return self.skills.get(name.lower(), 0)

    def skill_group(self, name: str) -> Optional[str]:
        """Optional: Returns the group this skill
        belongs to, or None if unknown."""
        return ALL_KNOWN_SKILLS.get(name.lower())

    def kill(self) -> None:
        self.state = "Dead"

    def get_state(self) -> str:
        return self.state
