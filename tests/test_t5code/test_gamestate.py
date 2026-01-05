"""Tests for loading and parsing game data files (maps and ship classes)."""

import io
from t5code import (
    load_and_parse_t5_map_filelike,
    load_and_parse_t5_ship_classes_filelike,
)
from t5code.T5Tables import SECTORS


def test_load_and_parse_t5_map_filelike():
    """Verify T5 map file parsing from file-like object."""
    mock_data = (
        "Name\tUWP\tZone\tSector\tSS\tHex\tRemarks\t{Ix}\n"
        "Regina\tA788899-C\tR\tSpinward Marches\tC\t1234\tHi In\t{2}\n"
        "Efate\tA000989-C\tA\tSpinward Marches\tA\t2345\tNa Pi\t{1}\n"
    )
    fake_file = io.StringIO(mock_data)
    result = load_and_parse_t5_map_filelike(fake_file)
    assert result["Regina"]["UWP"] == "A788899-C"
    assert result["Regina"]["Sector"] == "Regina"
    assert result["Efate"]["Coordinates"] == (23, 45)
    assert result["Efate"]["Sector"] == "Cronor"


def test_load_and_parse_t5_ship_classes_filelike():
    """Verify ship class CSV parsing from file-like object."""
    mock_data = (
        "class_name,jump_rating,maneuver_rating,"
        "cargo_capacity,staterooms,low_berths\n"
        "test_ship_class,5,3,20000,5,9\n"
        "test_nothing_class,2,3,53,29,3\n"
    )
    fake_file = io.StringIO(mock_data)
    result = load_and_parse_t5_ship_classes_filelike(fake_file)
    assert result["test_ship_class"]["jump_rating"] == 5
    assert result["test_nothing_class"]["cargo_capacity"] == 53


def test_sector_lookup_in_sectors_table():
    """Verify Sector field is looked up in SECTORS table."""
    mock_data = (
        "Name\tUWP\tZone\tSector\tSS\tHex\tRemarks\t{Ix}\n"
        "Test World\tA788899-C\tR\tSpin\tH\t1234\tHi In\t{2}\n"
    )
    fake_file = io.StringIO(mock_data)
    result = load_and_parse_t5_map_filelike(fake_file)
    # SS code H should map to Rhylanor in SECTORS table
    assert result["Test World"]["Sector"] == "Rhylanor"
    assert result["Test World"]["Sector"] == SECTORS["H"]


def test_sector_lookup_fallback_unknown_code():
    """Verify unknown sector codes fall back to original value."""
    mock_data = (
        "Name\tUWP\tZone\tSector\tSS\tHex\tRemarks\t{Ix}\n"
        "Test World\tA788899-C\tR\tUnknownSector\tZ\t1234\tHi\t{2}\n"
    )
    fake_file = io.StringIO(mock_data)
    result = load_and_parse_t5_map_filelike(fake_file)
    # Unknown SS code Z should remain as-is
    assert result["Test World"]["Sector"] == "Z"


def test_sector_lookup_multiple_worlds():
    """Verify sector lookup works for multiple worlds with diff codes."""
    mock_data = (
        "Name\tUWP\tZone\tSector\tSS\tHex\tRemarks\t{Ix}\n"
        "World A\tA788899-C\tR\tSpin\tA\t1234\tHi In\t{2}\n"
        "World B\tB000989-C\tA\tSpin\tK\t2345\tNa Pi\t{1}\n"
        "World C\tC000989-C\tG\tSpin\tG\t3456\tNa\t{0}\n"
    )
    fake_file = io.StringIO(mock_data)
    result = load_and_parse_t5_map_filelike(fake_file)
    assert result["World A"]["Sector"] == SECTORS["A"]  # Cronor
    assert result["World B"]["Sector"] == SECTORS["K"]  # Lunion
    assert result["World C"]["Sector"] == SECTORS["G"]  # Lanth
    assert result["World A"]["Sector"] == "Cronor"
    assert result["World B"]["Sector"] == "Lunion"
    assert result["World C"]["Sector"] == "Lanth"
