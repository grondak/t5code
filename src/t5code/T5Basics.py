"""Traveller 5 core mechanics and utility functions.

Provides basic T5 rules helpers including technology level conversion,
ability checks, and flux rolls.
"""

import random
from typing import Dict, Optional


def letter_to_tech_level(char: str) -> int:
    """
    Decodes a single Tech Level character (0-Z) to its integer value.
    Characters '0-9' map to 0-9, and 'A-Z' map to 10-35.

    Args:
        char (str): A single character representing the Tech Level.

    Returns:
        int: The integer value of the Tech Level.
    """
    if "0" <= char <= "9":  # For '0' to '9'
        return ord(char) - ord("0")
    elif "A" <= char <= "Z":  # For 'A' to 'Z'
        return ord(char) - ord("A") + 10
    else:
        raise ValueError(
            "Invalid Tech Level character. Must be in the"
            " range '0'-'9' or 'A'-'Z'."
        )


def tech_level_to_letter(value: int) -> str:
    """
    Encodes an integer value (0-35) into its corresponding
    Tech Level character (0-Z).
    Integers 0-9 map to '0'-'9', and 10-35 map to 'A'-'Z'.

    Args:
        value (int): An integer between 0 and 35.

    Returns:
        str: The corresponding Tech Level character.
    """
    if 0 <= value <= 9:  # For 0-9
        return chr(ord("0") + value)
    elif 10 <= value <= 35:  # For 10-35
        return chr(ord("A") + value - 10)
    else:
        raise ValueError(
            "Invalid Tech Level value. Must be an integer between 0 and 35."
        )


def check_success(roll_override: Optional[int] = None,
                  skills_override: Optional[Dict[str, int]] = None) -> bool:
    mod = sum(skills_override.values()) if skills_override is not None else 0
    roll = (
        roll_override
        if roll_override is not None
        else random.randint(1, 6) + random.randint(1, 6)
    )
    return (roll + mod) >= 8


def roll_flux() -> int:
    die1 = random.randint(1, 6)
    die2 = random.randint(1, 6)
    return die1 - die2


class SequentialFlux:
    """A two-stage flux roll where the first die is rolled immediately
    and the second die can be optionally rolled later.

    This allows for conditional logic between the two rolls.

    Example:
        flux = SequentialFlux()
        print(f"First die: {flux.first_die}")

        if some_condition:
            result = flux.roll_second()
            print(f"Final flux: {result}")
    """

    def __init__(self, first_die: Optional[int] = None):
        """Initialize with a first die roll.

        Args:
            first_die: Optional fixed value for first die (for testing).
                      If None, rolls 1d6.
        """
        self.first_die: int = (
            first_die if first_die is not None
            else random.randint(1, 6)
        )
        self.second_die: Optional[int] = None
        self._result: Optional[int] = None

    def roll_second(self, second_die: Optional[int] = None) -> int:
        """Roll the second die and compute the flux result.

        Args:
            second_die: Optional fixed value for second die (for testing).
                       If None, rolls 1d6.

        Returns:
            The flux result (first_die - second_die)
        """
        self.second_die = (
            second_die if second_die is not None
            else random.randint(1, 6)
        )
        self._result = self.first_die - self.second_die
        return self._result

    @property
    def result(self) -> Optional[int]:
        """Get the computed flux result, "
        "or None if second die not rolled yet."""
        return self._result

    @property
    def potential_range(self) -> tuple[int, int]:
        """Get the possible range of outcomes if second die is rolled.

        Returns:
            (min_possible, max_possible) tuple
        """
        min_flux = self.first_die - 6  # Best case for second die
        max_flux = self.first_die - 1  # Worst case for second die
        return (min_flux, max_flux)

    def __repr__(self) -> str:
        if self.second_die is None:
            return f"SequentialFlux(first={self.first_die}, pending)"
        return f"SequentialFlux(first={self.first_die}, " \
               f"second={self.second_die}, result={self._result})"
