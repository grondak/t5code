import io
from t5code import (
    load_and_parse_t5_map_filelike,
    load_and_parse_t5_ship_classes_filelike,
)


def test_load_and_parse_t5_map_filelike():
    mock_data = (
        "Name\tUWP\tZone\tHex\tRemarks\t{Ix}\n"
        "Regina\tA788899-C\tR\t1234\tHi In\t{2}\n"
        "Efate\tA000989-C\tA\t2345\tNa Pi\t{1}\n"
    )
    fake_file = io.StringIO(mock_data)
    result = load_and_parse_t5_map_filelike(fake_file)
    assert result["Regina"]["UWP"] == "A788899-C"
    assert result["Efate"]["Coordinates"] == (23, 45)


def test_load_and_parse_t5_ship_classes_filelike():
    mock_data = (
        "class_name,jump_rating,maneuver_rating,cargo_capacity\n"
        "test_ship_class,5,3,20000\n"
        "test_nothing_class,2,3,53\n"
    )
    fake_file = io.StringIO(mock_data)
    result = load_and_parse_t5_ship_classes_filelike(fake_file)
    assert result["test_ship_class"]["jump_rating"] == 5
    assert result["test_nothing_class"]["cargo_capacity"] == 53
