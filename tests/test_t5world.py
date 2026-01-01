"""Tests for world representation, starports,
populations, and broker selection."""

import pytest
from t5code.T5World import T5World, find_best_broker
from t5code.GameState import GameState
from t5code.T5Lot import T5Lot

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


def test_generate_speculative_cargo_total_tonnage():
    """Verify speculative cargo totals exactly 100 tons."""
    gs = GameState()
    gs.world_data = T5World.load_all_worlds(test_world_data)

    world = T5World("Earth", test_world_data)
    lots = world.generate_speculative_cargo(gs)

    total_mass = sum(lot.mass for lot in lots)
    assert total_mass == 100, f"Expected 100 tons, got {total_mass}"


def test_generate_speculative_cargo_lot_size_limit():
    """Verify individual lots don't exceed 10 tons."""
    gs = GameState()
    gs.world_data = T5World.load_all_worlds(test_world_data)

    world = T5World("Earth", test_world_data)
    lots = world.generate_speculative_cargo(gs)

    for lot in lots:
        assert lot.mass <= 10, f"Lot {lot.serial} exceeds 10 tons: {lot.mass}"


def test_generate_speculative_cargo_minimum_lot_size():
    """Verify all lots have at least 1 ton."""
    gs = GameState()
    gs.world_data = T5World.load_all_worlds(test_world_data)

    world = T5World("Earth", test_world_data)
    lots = world.generate_speculative_cargo(gs)

    for lot in lots:
        assert lot.mass >= 1, f"Lot {lot.serial} "
        f"is less than 1 ton: {lot.mass}"


def test_generate_speculative_cargo_custom_max_total():
    """Verify custom max_total_tons parameter works."""
    gs = GameState()
    gs.world_data = T5World.load_all_worlds(test_world_data)

    world = T5World("Earth", test_world_data)
    lots = world.generate_speculative_cargo(gs, max_total_tons=50)

    total_mass = sum(lot.mass for lot in lots)
    assert total_mass == 50, f"Expected 50 tons, got {total_mass}"


def test_generate_speculative_cargo_custom_max_lot_size():
    """Verify custom max_lot_size parameter works."""
    gs = GameState()
    gs.world_data = T5World.load_all_worlds(test_world_data)

    world = T5World("Earth", test_world_data)
    lots = world.generate_speculative_cargo(gs, max_lot_size=5)

    for lot in lots:
        assert lot.mass <= 5, f"Lot {lot.serial} exceeds 5 tons: {lot.mass}"

    total_mass = sum(lot.mass for lot in lots)
    assert total_mass == 100


def test_generate_speculative_cargo_lot_properties():
    """Verify generated lots have correct origin properties."""
    gs = GameState()
    gs.world_data = T5World.load_all_worlds(test_world_data)

    world = T5World("Earth", test_world_data)
    lots = world.generate_speculative_cargo(gs)

    for lot in lots:
        assert lot.origin_name == "Earth"
        assert lot.origin_uwp == "A123456-A"
        assert isinstance(lot, T5Lot)
        assert lot.serial  # Has unique ID


def test_generate_speculative_cargo_multiple_worlds():
    """Integration test: verify speculative cargo from different worlds."""
    gs = GameState()
    gs.world_data = T5World.load_all_worlds(test_world_data)

    # Generate from Earth
    earth = T5World("Earth", test_world_data)
    earth_lots = earth.generate_speculative_cargo(gs, max_total_tons=30)

    # Generate from Mars
    mars = T5World("Mars", test_world_data)
    mars_lots = mars.generate_speculative_cargo(gs, max_total_tons=30)

    # Verify origins are correct
    assert all(lot.origin_name == "Earth" for lot in earth_lots)
    assert all(lot.origin_name == "Mars" for lot in mars_lots)

    # Verify totals
    assert sum(lot.mass for lot in earth_lots) == 30
    assert sum(lot.mass for lot in mars_lots) == 30


def test_generate_speculative_cargo_realistic_scenario():
    """Integration test: realistic captain buying scenario."""
    gs = GameState()
    gs.world_data = T5World.load_all_worlds(test_world_data)

    # Captain at Earth wants to leave soon, buys speculative cargo
    world = T5World("Earth", test_world_data)
    available_cargo = world.generate_speculative_cargo(gs)

    # Captain has 82 ton cargo hold
    ship_capacity = 82
    purchased_lots = []
    total_purchased = 0

    for lot in available_cargo:
        if total_purchased + lot.mass <= ship_capacity:
            purchased_lots.append(lot)
            total_purchased += lot.mass

    # Verify captain can purchase lots without exceeding capacity
    assert total_purchased <= ship_capacity
    assert len(purchased_lots) > 0

    # Verify all purchased lots have valid properties
    for lot in purchased_lots:
        assert lot.origin_value > 0
        assert 1 <= lot.mass <= 10
