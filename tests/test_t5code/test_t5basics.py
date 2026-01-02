"""Tests for Traveller 5 core mechanics
(tech levels, ability checks, flux rolls)."""

import pytest
from unittest.mock import patch
from t5code.T5Basics import (
    letter_to_tech_level,
    tech_level_to_letter,
    check_success,
    roll_flux,
    SequentialFlux,
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


# ============================================================================
# SequentialFlux Tests
# ============================================================================


def test_sequential_flux_initialization():
    """Verify SequentialFlux initializes with first die rolled."""
    flux = SequentialFlux()
    assert 1 <= flux.first_die <= 6
    assert flux.second_die is None
    assert flux.result is None


def test_sequential_flux_fixed_first_die():
    """Verify SequentialFlux can be initialized with fixed first die."""
    flux = SequentialFlux(first_die=4)
    assert flux.first_die == 4
    assert flux.second_die is None
    assert flux.result is None


def test_sequential_flux_roll_second():
    """Verify rolling second die computes correct flux result."""
    flux = SequentialFlux(first_die=5)
    result = flux.roll_second(second_die=2)

    assert flux.second_die == 2
    assert result == 3  # 5 - 2
    assert flux.result == 3


def test_sequential_flux_roll_second_random():
    """Verify rolling second die without override uses random value."""
    flux = SequentialFlux(first_die=4)
    result = flux.roll_second()

    assert 1 <= flux.second_die <= 6
    assert result == flux.first_die - flux.second_die
    assert flux.result == result


def test_sequential_flux_potential_range():
    """Verify potential_range calculates correct min/max outcomes."""
    # First die = 1: range should be (-5, 0)
    flux1 = SequentialFlux(first_die=1)
    assert flux1.potential_range == (-5, 0)

    # First die = 3: range should be (-3, 2)
    flux3 = SequentialFlux(first_die=3)
    assert flux3.potential_range == (-3, 2)

    # First die = 6: range should be (0, 5)
    flux6 = SequentialFlux(first_die=6)
    assert flux6.potential_range == (0, 5)


def test_sequential_flux_all_subtables():
    """Verify all six sub-tables produce correct ranges."""
    expected_ranges = {
        1: (-5, 0),
        2: (-4, 1),
        3: (-3, 2),
        4: (-2, 3),
        5: (-1, 4),
        6: (0, 5),
    }

    for first_die, expected_range in expected_ranges.items():
        flux = SequentialFlux(first_die=first_die)
        assert flux.potential_range == expected_range


def test_sequential_flux_max_positive():
    """Verify sequential flux can achieve maximum positive value (+5)."""
    flux = SequentialFlux(first_die=6)
    result = flux.roll_second(second_die=1)
    assert result == 5


def test_sequential_flux_max_negative():
    """Verify sequential flux can achieve maximum negative value (-5)."""
    flux = SequentialFlux(first_die=1)
    result = flux.roll_second(second_die=6)
    assert result == -5


def test_sequential_flux_zero_outcomes():
    """Verify sequential flux can achieve zero from multiple paths."""
    # Path 1: 1-1 = 0
    flux1 = SequentialFlux(first_die=1)
    assert flux1.roll_second(second_die=1) == 0

    # Path 2: 3-3 = 0
    flux2 = SequentialFlux(first_die=3)
    assert flux2.roll_second(second_die=3) == 0

    # Path 3: 6-6 = 0
    flux3 = SequentialFlux(first_die=6)
    assert flux3.roll_second(second_die=6) == 0


def test_sequential_flux_result_before_roll():
    """Verify result is None before second die is rolled."""
    flux = SequentialFlux(first_die=4)
    assert flux.result is None


def test_sequential_flux_result_after_roll():
    """Verify result is available after second die is rolled."""
    flux = SequentialFlux(first_die=4)
    flux.roll_second(second_die=2)
    assert flux.result == 2


def test_sequential_flux_repr_pending():
    """Verify repr shows pending status before second roll."""
    flux = SequentialFlux(first_die=3)
    repr_str = repr(flux)
    assert "first=3" in repr_str
    assert "pending" in repr_str


def test_sequential_flux_repr_complete():
    """Verify repr shows complete status after second roll."""
    flux = SequentialFlux(first_die=5)
    flux.roll_second(second_die=2)
    repr_str = repr(flux)
    assert "first=5" in repr_str
    assert "second=2" in repr_str
    assert "result=3" in repr_str


def test_sequential_flux_multiple_instances_independent():
    """Verify multiple SequentialFlux instances don't interfere."""
    flux1 = SequentialFlux(first_die=2)
    flux2 = SequentialFlux(first_die=5)

    result1 = flux1.roll_second(second_die=1)
    result2 = flux2.roll_second(second_die=3)

    assert flux1.result == 1  # 2-1
    assert flux2.result == 2  # 5-3
    assert result1 != result2


@patch("random.randint")
def test_sequential_flux_random_first_die(mock_randint):
    """Verify first die uses random.randint when not provided."""
    mock_randint.return_value = 4
    flux = SequentialFlux()
    assert flux.first_die == 4
    mock_randint.assert_called_once_with(1, 6)


@patch("random.randint")
def test_sequential_flux_random_second_die(mock_randint):
    """Verify second die uses random.randint when not provided."""
    mock_randint.return_value = 3
    flux = SequentialFlux(first_die=5)
    result = flux.roll_second()
    assert flux.second_die == 3
    assert result == 2  # 5-3
    mock_randint.assert_called_once_with(1, 6)


def test_sequential_flux_deferred_decision():
    """Verify deferred second roll allows decision-making."""
    flux = SequentialFlux(first_die=2)

    # Check first die before committing
    if flux.first_die <= 3:
        # Low first die, don't roll second
        assert flux.result is None
    else:
        # High first die, would roll second
        flux.roll_second()

    # In this case, we didn't roll second
    assert flux.second_die is None
