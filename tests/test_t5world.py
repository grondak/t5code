"""Tests for world representation, starports,
populations, and broker selection."""

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


def test_uwp():
    """Verify world Universal World Profile (UWP) is retrieved correctly."""
    test_world = T5World("Earth", test_world_data)
    assert test_world.uwp() == "A123456-A"

    with pytest.raises(
        ValueError,
        match=r"Specified world Bogus is not in provided worlds table",
    ):
        T5World("Bogus", test_world_data)


def test_trade_classifications():
    """Verify world trade classifications are retrieved correctly."""
    test_world = T5World("Earth", test_world_data)
    assert test_world.trade_classifications() == "Ag As"


def test_importance():
    """Verify world importance value is retrieved correctly."""
    test_world = T5World("Earth", test_world_data)
    assert test_world.importance() == 4


def test_importance_negative():
    """Verify world importance can be negative."""
    test_world = T5World("Mars", test_world_data)
    assert test_world.importance() == -1


def test_load_all_worlds():
    """Verify factory method loads all worlds from data dict."""
    test_worlds = T5World.load_all_worlds(test_world_data)
    assert len(test_worlds) == 2
    assert all(isinstance(w, T5World) for w in test_worlds.values())


def test_get_starport_type():
    """Verify starport tier is extracted from UWP."""
    test_world = T5World("Earth", test_world_data)
    assert test_world.get_starport() == "A"


def test_get_population():
    """Verify population digit is extracted from UWP."""
    test_world = T5World("Earth", test_world_data)
    assert test_world.get_population() == 4


def test_get_population_mars():
    """Verify population extraction for different world."""
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
