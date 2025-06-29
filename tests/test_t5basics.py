import pytest
from unittest.mock import patch
from t5code.T5Basics import (
    letter_to_tech_level,
    tech_level_to_letter,
    check_success,
    roll_flux,
)


def test_letter_to_tech_level_valid():
    assert letter_to_tech_level("F") == 15
    assert letter_to_tech_level("3") == 3


def test_letter_to_tech_level_invalid():
    with pytest.raises(Exception) as excinfo:
        letter_to_tech_level("fail")
    assert (
        "Invalid Tech Level character. Must be in the range '0'-'9' or 'A'-'Z'."
        in str(excinfo.value)
    )


def test_tech_level_to_letter_valid():
    assert tech_level_to_letter(15) == "F"
    assert tech_level_to_letter(3) == "3"


@pytest.mark.parametrize("bad_value", [95, -3])
def test_tech_level_to_letter_invalid(bad_value):
    with pytest.raises(Exception) as excinfo:
        tech_level_to_letter(bad_value)
    assert "Invalid Tech Level value. Must be an integer between 0 and 35." in str(
        excinfo.value
    )


def test_check_success_basic():
    assert check_success(roll_override=9) is True
    assert check_success(roll_override=7) is False
    skills = dict([("medic", 3)])
    assert check_success(roll_override=8, skills_override=skills)


@patch("random.randint")
def test_flux_max_positive(mock_randint):
    mock_randint.side_effect = [6, 1]  # die1=6, die2=1
    assert roll_flux() == 5


@patch("random.randint")
def test_flux_zero(mock_randint):
    mock_randint.side_effect = [3, 3]
    assert roll_flux() == 0


@patch("random.randint")
def test_flux_max_negative(mock_randint):
    mock_randint.side_effect = [1, 6]
    assert roll_flux() == -5


@patch("random.randint")
def test_flux_edge_case(mock_randint):
    mock_randint.side_effect = [2, 5]
    assert roll_flux() == -3


def test_flux_distribution_bounds():
    """Run many rolls and ensure result is always between -5 and +5."""
    for _ in range(1000):
        result = roll_flux()
        assert -5 <= result <= 5
