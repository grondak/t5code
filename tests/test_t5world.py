import pytest
from t5code.T5World import T5World, find_best_broker

test_world_data = {
    "Earth": {
        "UWP": "A123456-A",
        "TradeClassifications": "Ag As",
        "Importance": 4,
    },
    "Mars": {
        "UWP": "B222222-B",
        "TradeClassifications": "Ba De",
        "Importance": -1,
    },
}


def test_UWP():
    test_world = T5World("Earth", test_world_data)
    assert test_world.UWP() == "A123456-A"
    with pytest.raises(Exception) as excinfo:
        T5World("Bogus", test_world_data)
    assert "Specified world Bogus is not in provided worlds table" in str(excinfo.value)


def test_trade_classifications():
    test_world = T5World("Earth", test_world_data)
    assert test_world.trade_classifications() == "Ag As"


def test_importance():
    test_world = T5World("Earth", test_world_data)
    assert test_world.importance() == 4


def test_importance_negative():
    test_world = T5World("Mars", test_world_data)
    assert test_world.importance() == -1


def test_load_all_worlds():
    test_worlds = T5World.load_all_worlds(test_world_data)
    assert len(test_worlds) == 2
    assert all(isinstance(w, T5World) for w in test_worlds.values())


def test_get_starport_type():
    test_world = T5World("Earth", test_world_data)
    assert test_world.get_starport() == "A"


def test_get_population():
    test_world = T5World("Earth", test_world_data)
    assert test_world.get_population() == 4


def test_get_population_mars():
    test_world = T5World("Mars", test_world_data)
    assert test_world.get_population() == 2


@pytest.mark.parametrize(
    "tier,expected",
    [
        ("A", {"name": "Broker-7+", "mod": 4, "rate": 0.2}),
        ("B", {"name": "Broker-6", "mod": 3, "rate": 0.15}),
        ("C", {"name": "Broker-4", "mod": 2, "rate": 0.1}),
        ("D", {"name": "Broker-2", "mod": 1, "rate": 0.05}),
    ],
)
def test_find_best_broker_tiers(tier, expected):
    assert find_best_broker(tier) == expected


def test_invalid_tier():
    with pytest.raises(ValueError):
        find_best_broker("E")


def test_trade_classifications_mars():
    test_world = T5World("Mars", test_world_data)
    assert test_world.trade_classifications() == "Ba De"


def test_get_starport_type_mars():
    test_world = T5World("Mars", test_world_data)
    assert test_world.get_starport() == "B"
