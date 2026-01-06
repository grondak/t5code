"""Non-player character (NPC) representation for Traveller 5.

Defines the T5NPC class for creating and managing NPCs with skills,
used for crew and passenger roles aboard starships.
"""

import uuid
import random
from typing import Dict, Optional
from t5code.T5Tables import SKILLS_BY_GROUP

ALL_KNOWN_SKILLS = {
    skill.lower(): group_name
    for group_name, skills in SKILLS_BY_GROUP.items()
    for skill in skills
}


def generate_captain_risk_profile() -> float:
    """Generate cargo departure threshold based on captain risk profile.

    Creates realistic distribution of captain behavior:
    - 60% chance: Standard (0.80) - cautious but practical
    - 30% chance: Moderate (0.70-0.90) - normal variance
    - 8% chance: Very cautious (0.91-0.95) - waits for full holds
    - 2% chance: Aggressive (0.65-0.69) - leaves early for speed

    Range is constrained to 0.60-0.98 to ensure reasonable behavior.

    Returns:
        Float between 0.60 and 0.98 representing cargo fill threshold

    Example:
        >>> threshold = generate_captain_risk_profile()
        >>> 0.60 <= threshold <= 0.98
        True
    """
    roll = random.random()

    if roll < 0.60:
        # 60% chance: Standard threshold
        return 0.80
    elif roll < 0.90:
        # 30% chance: Moderate range (70-90%)
        return random.uniform(0.70, 0.90)
    elif roll < 0.98:
        # 8% chance: Very cautious (91-95%)
        return random.uniform(0.91, 0.95)
    else:
        # 2% chance: Aggressive (65-69%)
        return random.uniform(0.65, 0.69)


class T5NPC:
    """Non-player character with skills and state tracking.

    NPCs can serve as crew members or passengers aboard starships. They have
    skills, locations, and states (alive, dead, missing). Skills are validated
    against a known list from T5 rules.

    Attributes:
        character_name: Character's name
        serial: Unique UUID identifier
        location: Current world/location name
        skills: Dictionary mapping skill names to levels
        state: Character state ('Alive', 'Dead', 'Missing', etc.)

    Example:
        >>> npc = T5NPC("Captain Reynolds")
        >>> npc.set_skill("Pilot", 3)
        >>> npc.set_skill("Leadership", 2)
        >>> print(npc.get_skill("pilot"))  # Case insensitive
        3
    """

    def __init__(self, character_name: str) -> None:
        """Create a new NPC.

        Args:
            character_name: Name of the character
        """
        # Core identity
        self.character_name: str = character_name
        self.serial: str = str(uuid.uuid4())  # Unique persistent ID

        # Starting attributes
        self.location: str = "Unknown"  # Assigned when first decided
        self.skills: Dict[str, int] = {}  # e.g. {"broker": 2, "gun combat": 1}
        self.state: str = "Alive"  # Could be "Alive", "Missing", "Dead", etc.

        # Captain/operational preferences
        # Won't depart until hold is this full
        self.cargo_departure_threshold: float = 0.8

    def update_location(self, location: str) -> None:
        """Update character's current location.

        Args:
            location: World name or location string
        """
        self.location = location

    def set_skill(self, name: str, level: int) -> None:
        """Set a skill to a specific level.

        Args:
            name: Skill name (case insensitive)
            level: Skill level (typically 0-5)

        Raises:
            ValueError: If skill name is not in the known skills list
        """
        key = name.lower()
        if key not in ALL_KNOWN_SKILLS:
            raise ValueError(f"Unknown skill: '{name}'")
        self.skills[key] = level

    def get_skill(self, name: str) -> int:
        """Get current level of a skill.

        Args:
            name: Skill name (case insensitive)

        Returns:
            Skill level (0 if character doesn't have the skill)
        """
        return self.skills.get(name.lower(), 0)

    def skill_group(self, name: str) -> Optional[str]:
        """Get the skill group a skill belongs to.

        Skills are organized into groups like 'Combat', 'Technical', etc.

        Args:
            name: Skill name (case insensitive)

        Returns:
            Skill group name, or None if skill is unknown
        """
        return ALL_KNOWN_SKILLS.get(name.lower())

    def kill(self) -> None:
        """Mark character as dead.

        Sets the character's state to 'Dead'. Used for mortality mechanics
        like low passage revival failures.
        """
        self.state = "Dead"
