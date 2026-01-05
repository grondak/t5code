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
    """Test that invalid starport tiers default to D tier."""
    # Non-standard starports should default to D tier
    broker_e = find_best_broker("E")
    broker_d = find_best_broker("D")
    assert broker_e == broker_d


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


def test_high_passenger_availability():
    """Test high passenger availability with Steward skill."""
    world = T5World("Earth", test_world_data)

    # Multiple rolls to test variation
    results = [world.high_passenger_availability(steward_skill=0)
               for _ in range(10)]

    # Should have variation (not all the same)
    assert len(set(results)) > 1

    # All results should be non-negative
    assert all(r >= 0 for r in results)


def test_mid_passenger_availability():
    """Test mid passenger availability with Admin skill."""
    world = T5World("Earth", test_world_data)

    # Multiple rolls to test variation
    results = [world.mid_passenger_availability(admin_skill=0)
               for _ in range(10)]

    # Should have variation (not all the same)
    assert len(set(results)) > 1

    # All results should be non-negative
    assert all(r >= 0 for r in results)


def test_low_passenger_availability():
    """Test low passenger availability with Streetwise skill."""
    world = T5World("Earth", test_world_data)

    # Multiple rolls to test variation
    results = [world.low_passenger_availability(streetwise_skill=0)
               for _ in range(10)]

    # Should have variation (not all the same)
    assert len(set(results)) > 1

    # All results should be non-negative
    assert all(r >= 0 for r in results)


def test_passenger_availability_with_skills():
    """Test that higher skills increase passenger availability."""
    world = T5World("Earth", test_world_data)

    # Test with and without skills (use multiple samples)
    no_skill_high = [world.high_passenger_availability(0) for _ in range(20)]
    with_skill_high = [world.high_passenger_availability(3) for _ in range(20)]

    # Average with skill should be higher (skill adds 3 to each roll)
    assert sum(with_skill_high) / len(with_skill_high) > \
        sum(no_skill_high) / len(no_skill_high)


def test_passenger_availability_formula():
    """Test passenger availability uses Flux + Population + Skill."""
    world = T5World("Mars", test_world_data)  # Pop 2

    # With 0 skill, result should be Flux (range -5 to +5) + Pop (2)
    # So range is -3 to 7, but clamped to 0 minimum
    results = [world.high_passenger_availability(0) for _ in range(50)]

    # Maximum possible: 5 (max flux) + 2 (pop) = 7
    assert max(results) <= 7

    # Minimum: 0 (negative results clamped)
    assert min(results) >= 0

    # With skill +5, max should be 5 + 2 + 5 = 12
    skilled_results = [world.high_passenger_availability(5) for _ in range(50)]
    assert max(skilled_results) <= 12


def test_get_population_hex_digit():
    """Test get_population with hex digit (A=10, B=11, etc.)."""
    # UWP with population A (10)
    world_data = {"HighPop": {"UWP": "A000A00-D", "Zone": "G",
                              "TradeClassifications": "", "Importance": "+0"}}
    world = T5World("HighPop", world_data)
    assert world.get_population() == 10

    # UWP with population B (11)
    world_data2 = {"VeryHighPop": {"UWP": "A000B00-D", "Zone": "G",
                   "TradeClassifications": "", "Importance": "+0"}}
    world = T5World("VeryHighPop", world_data2)
    assert world.get_population() == 11


def test_full_name_with_subsector_and_hex():
    """Test full_name() returns formatted name with sector and hex."""
    world_data = {
        "Regina": {
            "UWP": "A788899-C",
            "Zone": "G",
            "Sector": "Regina",
            "Subsector": "C",
            "Hex": "1910",
            "TradeClassifications": "Ri Hi In",
            "Importance": "+4"
        }
    }
    world = T5World("Regina", world_data)
    assert world.full_name() == "Regina/Regina (1910)"


def test_full_name_without_subsector_or_hex():
    """Test full_name() falls back to name when subsector/hex missing."""
    world_data = {
        "Unknown": {
            "UWP": "X000000-0",
            "Zone": "R",
            "TradeClassifications": "",
            "Importance": "-1"
        }
    }
    world = T5World("Unknown", world_data)
    # Should fall back to just the name
    assert world.full_name() == "Unknown"


def test_subsector():
    """Test subsector() method returns correct value."""
    world_data = {
        "TestWorld": {
            "UWP": "A123456-A",
            "TradeClassifications": "Ag",
            "Importance": "2",
            "Subsector": "B"
        }
    }
    world = T5World("TestWorld", world_data)
    assert world.subsector() == "B"


def test_subsector_missing():
    """Test subsector() returns empty string when not present."""
    world_data = {
        "TestWorld": {
            "UWP": "A123456-A",
            "TradeClassifications": "Ag",
            "Importance": "2"
        }
    }
    world = T5World("TestWorld", world_data)
    assert world.subsector() == ""
