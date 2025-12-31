"""Traveller 5 core mechanics and utility functions.

Provides basic T5 rules helpers including technology level conversion,
ability checks, and flux rolls.
"""

import random


def letter_to_tech_level(char):
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


def tech_level_to_letter(value):
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


def check_success(roll_override: int = None,
                  skills_override: dict = None) -> bool:
    mod = sum(skills_override.values()) if skills_override is not None else 0
    roll = (
        roll_override
        if roll_override is not None
        else random.randint(1, 6) + random.randint(1, 6)
    )
    return (roll + mod) >= 8


def roll_flux():
    die1 = random.randint(1, 6)
    die2 = random.randint(1, 6)
    return die1 - die2
