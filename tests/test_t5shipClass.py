from t5code.T5ShipClass import T5ShipClass

test_ship_data = {
    "small": {
        "class_name": "small",
        "jump_rating": 1,
        "maneuver_rating": 2,
        "cargo_capacity": 10,
    },
    "large": {
        "class_name": "large",
        "jump_rating": 3,
        "maneuver_rating": 3,
        "cargo_capacity": 200,
    },
}


def test_USP():
    test_class = T5ShipClass("small", test_ship_data["small"])
    assert test_class.USP() == "small 12\nCargo: 10 tons"
    test_class2 = T5ShipClass("large", test_ship_data["large"])
    assert test_class2.USP() == "large 33\nCargo: 200 tons"


def test_load_all_ship_classes():
    test_classes = T5ShipClass.load_all_ship_classes(test_ship_data)
    assert len(test_classes) == 2
