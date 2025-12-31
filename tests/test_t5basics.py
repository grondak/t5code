"""Tests for Traveller 5 core mechanics
(tech levels, ability checks, flux rolls)."""

import pytest
from unittest.mock import patch
from t5code.T5Basics import (
    letter_to_tech_level,
    tech_level_to_letter,
    check_success,
    roll_flux,
)


def test_letter_to_tech_level_valid():
    """Verify letter-to-tech-level conversion works for letters and digits."""
    assert letter_to_tech_level("F") == 15
    assert letter_to_tech_level("3") == 3


def test_letter_to_tech_level_invalid():
    """Verify invalid characters raise appropriate exception."""
    with pytest.raises(Exception) as excinfo:
        letter_to_tech_level("fail")
    assert (
        "Invalid Tech Level character. "
        "Must be in the range '0'-'9' or 'A'-'Z'."
        in str(excinfo.value)
    )


def test_tech_level_to_letter_valid():
    """Verify tech-level-to-letter conversion works for values 0-35."""
    assert tech_level_to_letter(15) == "F"
    assert tech_level_to_letter(3) == "3"


@pytest.mark.parametrize("bad_value", [95, -3])
def test_tech_level_to_letter_invalid(bad_value):
    """Verify out-of-range tech levels raise exception."""
    with pytest.raises(Exception) as excinfo:
        tech_level_to_letter(bad_value)
    assert (
        "Invalid Tech Level value. "
        "Must be an integer between 0 and 35." in str(
            excinfo.value
        )
    )


def test_check_success_basic():
    """Verify ability checks pass/fail based on roll and skill modifiers."""
    assert check_success(roll_override=9) is True
    assert check_success(roll_override=7) is False
    skills = {"medic": 5}
    assert check_success(roll_override=8, skills_override=skills)


@patch("random.randint")
def test_flux_max_positive(mock_randint):
    """Verify flux roll achieves maximum positive value (+5)."""
    mock_randint.side_effect = [6, 1]
    assert roll_flux() == 5


@patch("random.randint")
def test_flux_zero(mock_randint):
    """Verify flux roll can result in zero."""
    mock_randint.side_effect = [3, 3]
    assert roll_flux() == 0


@patch("random.randint")
def test_flux_max_negative(mock_randint):
    """Verify flux roll achieves maximum negative value (-5)."""
    mock_randint.side_effect = [1, 6]
    assert roll_flux() == -5


@patch("random.randint")
def test_flux_edge_case(mock_randint):
    """Verify flux roll for edge case (2d6-1d6 = -3)."""
    mock_randint.side_effect = [2, 5]
    assert roll_flux() == -3


def test_flux_distribution_bounds():
    """Run many rolls and ensure result is always between -5 and +5."""
    for _ in range(1000):
        result = roll_flux()
        assert -5 <= result <= 5
