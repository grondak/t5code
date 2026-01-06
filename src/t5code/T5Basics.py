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
    """Perform a T5 ability check (roll 2d6, apply modifiers, target 8+).

    This is the core task resolution mechanic in Traveller 5. Characters roll
    2d6, add their skill levels, and try to meet or exceed a target number (8).

    Args:
        roll_override: Fixed dice value for testing (instead of rolling 2d6)
        skills_override: Dictionary of skill modifiers to apply

    Returns:
        True if (2d6 + skills) >= 8, False otherwise

    Example:
        >>> check_success(skills_override={"pilot": 2, "dexterity": 1})
        True  # If roll was 5+ (5+3 = 8)
    """
    mod = sum(skills_override.values()) if skills_override is not None else 0
    roll = (
        roll_override
        if roll_override is not None
        else random.randint(1, 6) + random.randint(1, 6)
    )
    return (roll + mod) >= 8


def roll_flux() -> int:
    """Roll flux (1d6 - 1d6) for random variation.

    Flux is used throughout T5 for random modifiers with a bell curve
    centered on zero. Results range from -5 to +5.

    Returns:
        Integer from -5 to +5, with 0 being most common

    Example:
        >>> flux = roll_flux()
        >>> passenger_count = base_count + flux + population_mod
    """
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


class TravellerCalendar:
    """Handles Traveller Imperial calendar with 13 months of 28 days.

    The Imperial calendar consists of:
    - Day 001: Holiday (not part of any month)
    - 13 months of 28 days each (364 days total)
    - Months begin on Day 002 and advance every 28 days

    Month boundaries:
    - Month 1: Days 002-029
    - Month 2: Days 030-057
    - Month 3: Days 058-085
    - Month 4: Days 086-113
    - Month 5: Days 114-141
    - Month 6: Days 142-169
    - Month 7: Days 170-197
    - Month 8: Days 198-225
    - Month 9: Days 226-253
    - Month 10: Days 254-281
    - Month 11: Days 282-309
    - Month 12: Days 310-337
    - Month 13: Days 338-365

    Example:
        >>> cal = TravellerCalendar()
        >>> cal.get_month(15)  # Day 015
        1
        >>> cal.get_first_day_of_month(2)  # Month 2
        30
        >>> cal.get_month_info(100)
        {'day': 100, 'month': 4, 'day_of_month': 15, 'is_holiday': False}
    """

    DAYS_PER_MONTH = 28
    NUM_MONTHS = 13
    HOLIDAY_DAY = 1
    FIRST_MONTH_START = 2  # Day 002
    _DAY_RANGE_ERROR = "Day of year must be between 1 and 365"

    def get_month(self, day_of_year: int) -> Optional[int]:
        """Get the month number (1-13) for a given day of year.

        Args:
            day_of_year: Day of year (1-365)

        Returns:
            Month number (1-13), or None if day is the Holiday (Day 001)

        Raises:
            ValueError: If day_of_year is not in range 1-365

        Example:
            >>> cal.get_month(1)  # Holiday
            None
            >>> cal.get_month(2)  # First day of Month 1
            1
            >>> cal.get_month(29)  # Last day of Month 1
            1
            >>> cal.get_month(30)  # First day of Month 2
            2
        """
        if not 1 <= day_of_year <= 365:
            raise ValueError(self._DAY_RANGE_ERROR)

        if day_of_year == self.HOLIDAY_DAY:
            return None

        # Calculate month: (day - 2) // 28 + 1
        # Day 2-29 -> Month 1, Day 30-57 -> Month 2, etc.
        month = ((day_of_year -
                  self.FIRST_MONTH_START) // self.DAYS_PER_MONTH) + 1
        return month

    def get_first_day_of_month(self, month: int) -> int:
        """Get the first day of year for a given month.

        Args:
            month: Month number (1-13)

        Returns:
            First day of year for that month (2-338)

        Raises:
            ValueError: If month is not in range 1-13

        Example:
            >>> cal.get_first_day_of_month(1)
            2
            >>> cal.get_first_day_of_month(2)
            30
            >>> cal.get_first_day_of_month(13)
            338
        """
        if not 1 <= month <= self.NUM_MONTHS:
            raise ValueError("Month must be between 1 and 13")

        return self.FIRST_MONTH_START + ((month - 1) * self.DAYS_PER_MONTH)

    def get_next_month_start(self, day_of_year: int) -> int:
        """Get the first day of the next month after the given day.

        Args:
            day_of_year: Current day of year (1-365)

        Returns:
            First day of the next month. If currently in Month 13 or on
            Holiday, returns 2 (first day of Month 1 of next year).

        Raises:
            ValueError: If day_of_year is not in range 1-365

        Example:
            >>> cal.get_next_month_start(1)  # Holiday
            2  # Start of Month 1
            >>> cal.get_next_month_start(15)  # In Month 1
            30  # Start of Month 2
            >>> cal.get_next_month_start(350)  # In Month 13
            2  # Start of Month 1 (next year)
        """
        if not 1 <= day_of_year <= 365:
            raise ValueError(self._DAY_RANGE_ERROR)

        current_month = self.get_month(day_of_year)

        # If Holiday or in Month 13, next month is Month 1
        if current_month is None or current_month == self.NUM_MONTHS:
            return self.FIRST_MONTH_START

        # Otherwise, return first day of next month
        return self.get_first_day_of_month(current_month + 1)

    def get_month_info(self, day_of_year: int) -> Dict[str, any]:
        """Get comprehensive month information for a given day.

        Args:
            day_of_year: Day of year (1-365)

        Returns:
            Dictionary containing:
            - 'day': Original day of year
            - 'month': Month number (1-13) or None if Holiday
            - 'day_of_month': Day within the month (1-28) or None if Holiday
            - 'is_holiday': True if Day 001

        Raises:
            ValueError: If day_of_year is not in range 1-365

        Example:
            >>> cal.get_month_info(1)
            {'day': 1, 'month': None, 'day_of_month': None, 'is_holiday': True}
            >>> cal.get_month_info(100)
            {'day': 100, 'month': 4, 'day_of_month': 15, 'is_holiday': False}
        """
        if not 1 <= day_of_year <= 365:
            raise ValueError(self._DAY_RANGE_ERROR)

        if day_of_year == self.HOLIDAY_DAY:
            return {
                'day': day_of_year,
                'month': None,
                'day_of_month': None,
                'is_holiday': True
            }

        month = self.get_month(day_of_year)
        first_day = self.get_first_day_of_month(month)
        day_of_month = day_of_year - first_day + 1

        return {
            'day': day_of_year,
            'month': month,
            'day_of_month': day_of_month,
            'is_holiday': False
        }

    def __repr__(self) -> str:
        return "TravellerCalendar(13 months × 28 days + Holiday)"
