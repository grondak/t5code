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
    TravellerCalendar,
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


# ============================================================================
# TravellerCalendar Tests
# ============================================================================

def test_traveller_calendar_holiday():
    """Test that Day 001 is recognized as Holiday with no month."""
    cal = TravellerCalendar()
    assert cal.get_month(1) is None

    info = cal.get_month_info(1)
    assert info['day'] == 1
    assert info['month'] is None
    assert info['day_of_month'] is None
    assert info['is_holiday'] is True


def test_traveller_calendar_month_boundaries():
    """Test month boundaries are correct for all 13 months."""
    cal = TravellerCalendar()

    # Month 1: Days 2-29
    assert cal.get_month(2) == 1
    assert cal.get_month(29) == 1
    assert cal.get_month(30) == 2

    # Month 2: Days 30-57
    assert cal.get_month(30) == 2
    assert cal.get_month(57) == 2
    assert cal.get_month(58) == 3

    # Month 13: Days 338-365
    assert cal.get_month(338) == 13
    assert cal.get_month(365) == 13


def test_traveller_calendar_get_first_day_of_month():
    """Test getting first day of each month."""
    cal = TravellerCalendar()

    assert cal.get_first_day_of_month(1) == 2
    assert cal.get_first_day_of_month(2) == 30
    assert cal.get_first_day_of_month(3) == 58
    assert cal.get_first_day_of_month(4) == 86
    assert cal.get_first_day_of_month(5) == 114
    assert cal.get_first_day_of_month(6) == 142
    assert cal.get_first_day_of_month(7) == 170
    assert cal.get_first_day_of_month(8) == 198
    assert cal.get_first_day_of_month(9) == 226
    assert cal.get_first_day_of_month(10) == 254
    assert cal.get_first_day_of_month(11) == 282
    assert cal.get_first_day_of_month(12) == 310
    assert cal.get_first_day_of_month(13) == 338


def test_traveller_calendar_get_next_month_start():
    """Test getting first day of next month."""
    cal = TravellerCalendar()

    # From Holiday -> Month 1
    assert cal.get_next_month_start(1) == 2

    # From Month 1 -> Month 2
    assert cal.get_next_month_start(15) == 30
    assert cal.get_next_month_start(29) == 30

    # From Month 2 -> Month 3
    assert cal.get_next_month_start(30) == 58
    assert cal.get_next_month_start(50) == 58

    # From Month 13 -> Month 1 (next year)
    assert cal.get_next_month_start(350) == 2
    assert cal.get_next_month_start(365) == 2


def test_traveller_calendar_get_month_info():
    """Test comprehensive month information."""
    cal = TravellerCalendar()

    # Test various days
    info = cal.get_month_info(100)
    assert info['day'] == 100
    assert info['month'] == 4
    # math for correct day of month 100 - 86 + 1 = 15
    assert info['day_of_month'] == 15
    assert info['is_holiday'] is False

    # First day of a month
    info = cal.get_month_info(30)
    assert info['month'] == 2
    assert info['day_of_month'] == 1

    # Last day of a month
    info = cal.get_month_info(57)
    assert info['month'] == 2
    assert info['day_of_month'] == 28


def test_traveller_calendar_invalid_day():
    """Test that invalid days raise ValueError."""
    cal = TravellerCalendar()

    with pytest.raises(ValueError,
                       match="Day of year must be between 1 and 365"):
        cal.get_month(0)

    with pytest.raises(ValueError,
                       match="Day of year must be between 1 and 365"):
        cal.get_month(366)

    with pytest.raises(ValueError):
        cal.get_month_info(-5)

    with pytest.raises(ValueError):
        cal.get_next_month_start(400)


def test_traveller_calendar_invalid_month():
    """Test that invalid month numbers raise ValueError."""
    cal = TravellerCalendar()

    with pytest.raises(ValueError, match="Month must be between 1 and 13"):
        cal.get_first_day_of_month(0)

    with pytest.raises(ValueError, match="Month must be between 1 and 13"):
        cal.get_first_day_of_month(14)


def test_traveller_calendar_all_days_have_month():
    """Test that every day 2-365 has a valid month."""
    cal = TravellerCalendar()

    for day in range(2, 366):
        month = cal.get_month(day)
        assert 1 <= month <= 13, (f"Day {day} should "
                                  f"have month 1-13, got {month}")


def test_traveller_calendar_repr():
    """Test string representation."""
    cal = TravellerCalendar()
    assert "13 months" in repr(cal)
    assert "28 days" in repr(cal)
