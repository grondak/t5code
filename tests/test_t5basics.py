import unittest
from unittest.mock import patch
import random
from T5Code.T5Basics import (
    letter_to_tech_level,
    tech_level_to_letter,
    check_success,
    roll_flux,
)


class TestT5Basics(unittest.TestCase):
    """Tests for the Swiss Army Knife Tech Debt Monster"""

    def test_letter_to_tech_level(self):
        tech_level_char = "F"
        decoded_value = letter_to_tech_level(tech_level_char)
        self.assertEqual(15, decoded_value)
        tech_level_char = "3"
        decoded_value = letter_to_tech_level(tech_level_char)
        self.assertEqual(3, decoded_value)
        tech_level_char = "fail"
        with self.assertRaises(Exception) as context:
            decoded_value = letter_to_tech_level(tech_level_char)
        self.assertTrue(
            "Invalid Tech Level character. Must be in the range '0'-'9' or 'A'-'Z'."
            in str(context.exception)
        )

    def test_tech_level_to_letter(self):
        tech_level = 15
        encoded_value = tech_level_to_letter(tech_level)
        self.assertEqual("F", encoded_value)
        tech_level = 3
        encoded_value = tech_level_to_letter(tech_level)
        self.assertEqual("3", encoded_value)
        tech_level = 95
        with self.assertRaises(Exception) as context:
            encoded_value = tech_level_to_letter(tech_level)
        self.assertTrue(
            "Invalid Tech Level value. Must be an integer between 0 and 35."
            in str(context.exception)
        )
        tech_level = -3
        with self.assertRaises(Exception) as context:
            encoded_value = tech_level_to_letter(tech_level)
        self.assertTrue(
            "Invalid Tech Level value. Must be an integer between 0 and 35."
            in str(context.exception)
        )

    def test_check_success(self):
        assert check_success(roll_override=9) is True
        assert check_success(roll_override=7) is False
        skills = dict([("medic", 3)])
        assert check_success(roll_override=8, skills_override=skills)

    @patch("random.randint")
    def test_flux_max_positive(self, mock_randint):
        mock_randint.side_effect = [6, 1]  # die1=6, die2=1
        self.assertEqual(roll_flux(), 5)

    @patch("random.randint")
    def test_flux_zero(self, mock_randint):
        mock_randint.side_effect = [3, 3]
        self.assertEqual(roll_flux(), 0)

    @patch("random.randint")
    def test_flux_max_negative(self, mock_randint):
        mock_randint.side_effect = [1, 6]
        self.assertEqual(roll_flux(), -5)

    @patch("random.randint")
    def test_flux_edge_case(self, mock_randint):
        mock_randint.side_effect = [2, 5]
        self.assertEqual(roll_flux(), -3)

    def test_flux_distribution_bounds(self):
        """Run many rolls and ensure result is always between -5 and +5."""
        for _ in range(1000):
            result = roll_flux()
            self.assertGreaterEqual(result, -5)
            self.assertLessEqual(result, 5)


if __name__ == "__main__":
    unittest.main()
