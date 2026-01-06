"""Tests for starship operations including crew, passengers,
cargo, and balance tracking."""

import pytest
from t5code.T5Starship import T5Starship
from t5code.T5Exceptions import (
    InsufficientFundsError,
    CapacityExceededError,
    InvalidPassageClassError,
    DuplicateItemError,
    WorldNotFoundError,
    InvalidLotTypeError,
    InvalidThresholdError,
)
from t5code.T5ShipClass import T5ShipClass
from t5code.T5NPC import T5NPC
from t5code.GameState import GameState, load_and_parse_t5_map
from t5code.T5Mail import T5Mail
from t5code.T5Lot import T5Lot
from t5code.T5World import T5World


@pytest.fixture
def test_ship_data():
    return {
        "small": {
            "class_name": "small",
            "jump_rating": 1,
            "maneuver_rating": 2,
            "cargo_capacity": 10,
            "staterooms": 2,
            "low_berths": 0,
        },
        "large": {
            "class_name": "large",
            "jump_rating": 3,
            "maneuver_rating": 3,
            "cargo_capacity": 200,
            "staterooms": 10,
            "low_berths": 50,
        },
    }


@pytest.fixture
def setup_test_gamestate():
    """Setup GameState for tests that need T5Lot or T5Mail."""
    MAP_FILE = "tests/test_t5code/t5_test_map.txt"
    GameState.world_data = T5World.load_all_worlds(
        load_and_parse_t5_map(MAP_FILE))
    return GameState


@pytest.fixture
def setup_gamestate():
    MAP_FILE = "tests/test_t5code/t5_test_map.txt"
    GameState.world_data = T5World.load_all_worlds(load_and_parse_t5_map(
        MAP_FILE))


@pytest.fixture
def basic_starship(test_ship_data, setup_gamestate):
    test_ship_class = T5ShipClass("small", test_ship_data["small"])
    ship = T5Starship("Steamboat", "Rhylanor", test_ship_class)

    ship.holdSize = 100
    ship.cargoSize = 0
    return ship


def get_me_a_starship(name, world, test_ship_data):
    test_ship_class = T5ShipClass("small", test_ship_data["small"])
    return T5Starship(name, world, test_ship_class)


def test_create_starship_with_name(test_ship_data):
    """Verify starship creation with name and default collections."""
    starship = get_me_a_starship("Your mom", "Home", test_ship_data)
    assert starship.ship_name == "Your mom"
    assert starship.passengers == {
        "all": set(),
        "high": set(),
        "low": set(),
        "mid": set(),
    }
    assert starship.mail == {}
    assert starship.location == "Home"
    assert starship.crew == {}


def test_hire_crew(test_ship_data):
    """Verify crew hiring with validation."""
    starship = get_me_a_starship("Your mom", "Home", test_ship_data)
    npc1 = T5NPC("Bob")
    # API is now flexible - allows any position string
    starship.hire_crew("custom_position", npc1)
    assert starship.crew == {"custom_position": npc1}

    # But still validates NPC type
    with pytest.raises(TypeError, match="Invalid NPC."):
        starship.hire_crew("medic", "a something")

    starship.hire_crew("medic", npc1)
    assert starship.crew["medic"] == npc1


def test_onload_passenger(test_ship_data):
    """Verify passenger boarding with duplicate detection."""
    starship = get_me_a_starship("Titanic", "Southampton", test_ship_data)
    with pytest.raises(TypeError, match="Invalid passenger type."):
        starship.onload_passenger("a string", "high")
    npc1 = T5NPC("Bob")
    with pytest.raises(InvalidPassageClassError):
        starship.onload_passenger(npc1, "yourmom")
    starship.onload_passenger(npc1, "high")
    assert {npc1} == starship.passengers["high"]
    npc2 = T5NPC("Doug")
    starship.onload_passenger(npc2, "high")
    assert {npc1, npc2} == starship.passengers["high"]
    with pytest.raises(DuplicateItemError):
        starship.onload_passenger(npc1, "high")
    assert {npc1, npc2} == starship.passengers["high"]
    assert npc1.location == starship.ship_name
    assert npc2.location == starship.ship_name


def test_offload_passengers(test_ship_data):
    """Verify passenger offloading by class with medic requirement."""
    # Use large ship with 10 staterooms and 50 low berths
    ship_class = T5ShipClass("large", test_ship_data["large"])
    starship = T5Starship("Pequod", "Nantucket", ship_class)
    npc1 = T5NPC("Bob")
    starship.onload_passenger(npc1, "high")
    npc2 = T5NPC("Doug")
    starship.onload_passenger(npc2, "high")
    npc3 = T5NPC("Bill")
    starship.onload_passenger(npc3, "mid")
    npc4 = T5NPC("Ted")
    starship.onload_passenger(npc4, "low")
    assert starship.passengers["high"] == {npc1, npc2}
    assert starship.passengers["mid"] == {npc3}
    assert starship.passengers["low"] == {npc4}
    offloaded_passengers = starship.offload_passengers("high")
    assert offloaded_passengers == {npc1, npc2}
    assert starship.passengers["high"] == set()
    assert npc1.location == starship.location
    assert npc2.location == starship.location
    with pytest.raises(InvalidPassageClassError):
        starship.offload_passengers("a something")
    offloaded_passengers = starship.offload_passengers("mid")
    assert offloaded_passengers == {npc3}
    assert starship.passengers["mid"] == set()
    assert npc3.location == starship.location
    npc5 = T5NPC("Bones")
    npc5.set_skill("Medic", 45)
    starship.hire_crew("medic", npc5)
    offloaded_passengers = starship.offload_passengers("low")
    assert offloaded_passengers == {npc4}
    assert starship.passengers["low"] == set()
    assert npc4.location == starship.location


def test_set_course_for(test_ship_data, setup_gamestate):
    """Verify destination setting and retrieval."""
    starship = get_me_a_starship("Steamboat", "Rhylanor", test_ship_data)
    starship.set_course_for("Jae Tellona")
    assert starship.destination == "Jae Tellona"


def test_onload_mail(test_ship_data, setup_gamestate):
    """Verify mail loading with capacity validation."""
    starship = get_me_a_starship("Steamboat", "Rhylanor", test_ship_data)
    mail = T5Mail("Rhylanor", "Jae Tellona", GameState)
    starship.onload_mail(mail)
    assert starship.mail_bundles[mail.serial] == mail
    with pytest.raises(ValueError,
                       match="Starship mail locker size exceeded."):
        for _ in range(6):
            mail = T5Mail("Rhylanor", "Jae Tellona", GameState)
            starship.onload_mail(mail)


def test_offload_mail(test_ship_data, setup_gamestate):
    """Verify mail offloading and empty state handling."""
    starship = get_me_a_starship("Steamboat", "Rhylanor", test_ship_data)
    mail = T5Mail("Rhylanor", "Jae Tellona", GameState)
    starship.onload_mail(mail)
    starship.offload_mail()
    assert len(starship.mail_bundles.keys()) == 0
    with pytest.raises(ValueError,
                       match="Starship has no mail to offload."):
        starship.offload_mail()


def test_awaken_passenger(test_ship_data):
    """Verify low berth awakening with medic skill check."""
    # Use large ship with 50 low berths
    ship_class = T5ShipClass("large", test_ship_data["large"])
    starship = T5Starship("Steamboat", "Rhylanor", ship_class)
    npc1 = T5NPC("Bones")
    npc1.set_skill("Medic", 3)
    starship.hire_crew("medic", npc1)
    npc2 = T5NPC("Ted")
    starship.onload_passenger(npc2, "low")
    assert starship.awaken_low_passenger(
        npc2,
        npc1,
        roll_override_in=20) is True
    assert npc2.state == "Alive"
    assert starship.awaken_low_passenger(
        npc2,
        npc1,
        roll_override_in=-20) is False
    assert npc2.state == "Dead"


def test_onload_lot(test_ship_data, setup_gamestate):
    """Verify cargo lot loading with capacity and duplication checking."""
    starship = get_me_a_starship("Steamboat", "Rhylanor", test_ship_data)
    lot = T5Lot("Rhylanor", GameState)
    lot.mass = 5000  # tons
    with pytest.raises(TypeError):
        starship.onload_lot("a string", "cargo")
    with pytest.raises(InvalidLotTypeError):
        starship.onload_lot(lot, "your mom")
    with pytest.raises(CapacityExceededError):
        starship.onload_lot(lot, "cargo")
    lot.mass = 5  # tons
    starship.onload_lot(lot, "freight")
    assert lot in starship.cargo_manifest["freight"]
    with pytest.raises(DuplicateItemError):
        starship.onload_lot(lot, "freight")
    with pytest.raises(DuplicateItemError):
        starship.onload_lot(lot, "cargo")
    lot2 = T5Lot("Rhylanor", GameState)
    lot2.mass = 5  # tons
    starship.onload_lot(lot2, "cargo")
    assert lot2 in starship.cargo_manifest["cargo"]
    lot3 = T5Lot("Rhylanor", GameState)
    with pytest.raises(CapacityExceededError):
        starship.onload_lot(lot3, "cargo")


def test_offload_lot(test_ship_data, setup_gamestate):
    """Verify cargo lot offloading and removal from cargo hold."""
    starship = get_me_a_starship("Steamboat", "Rhylanor", test_ship_data)
    lot = T5Lot("Rhylanor", GameState)
    lot.mass = 5
    starship.onload_lot(lot, "cargo")
    lot2 = T5Lot("Rhylanor", GameState)
    lot2.mass = 5
    starship.onload_lot(lot2, "cargo")
    assert lot in starship.cargo_manifest["cargo"]
    with pytest.raises(ValueError, match="Invalid lot serial number."):
        starship.offload_lot("your mom", "cargo")
    with pytest.raises(InvalidLotTypeError):
        starship.offload_lot(lot.serial, "your mom")
    with pytest.raises(ValueError, match="Lot not found as specified type."):
        starship.offload_lot(lot.serial, "freight")
    lot3 = starship.offload_lot(lot.serial, "cargo")
    is_still_there = any(
        lotIndex.serial ==
        lot3.serial for lotIndex in starship.cargo_manifest["cargo"]
    )
    assert lot.serial == lot3.serial
    assert not is_still_there
    assert len(starship.cargo_manifest["cargo"]) == 1


@pytest.fixture
def crewed_ship(test_ship_data, setup_gamestate):
    alice = T5NPC("Alice")
    bob = T5NPC("Bob")
    charlie = T5NPC("Charlie")
    alice.set_skill("Liaison", 2)
    bob.set_skill("Liaison", 5)
    charlie.set_skill("Liaison", 1)
    charlie.set_skill("Vacc Suit", 3)
    ship = get_me_a_starship("Steamboat", "Rhylanor", test_ship_data)
    ship.hire_crew("crew1", alice)
    ship.hire_crew("crew2", bob)
    ship.hire_crew("crew3", charlie)
    return ship


def test_initial_balance(crewed_ship):
    """Verify starship balance initializes to zero."""
    assert crewed_ship.balance == pytest.approx(0.0)


def test_credit_valid_amount(crewed_ship):
    """Verify crediting funds increases balance."""
    crewed_ship.credit(100)
    assert crewed_ship.balance == pytest.approx(100.0)


def test_debit_valid_amount(crewed_ship):
    """Verify debiting funds decreases balance."""
    crewed_ship.credit(200)
    crewed_ship.debit(50)
    assert crewed_ship.balance == pytest.approx(150.0)


def test_credit_invalid_type(crewed_ship):
    """Verify crediting non-numeric raises TypeError."""
    with pytest.raises(TypeError):
        crewed_ship.credit("not money")


def test_debit_invalid_type(crewed_ship):
    """Verify debiting non-numeric raises TypeError."""
    with pytest.raises(TypeError):
        crewed_ship.debit(None)


def test_credit_negative_amount(crewed_ship):
    """Verify crediting negative amount raises ValueError."""
    with pytest.raises(ValueError):
        crewed_ship.credit(-10)


def test_debit_negative_amount(crewed_ship):
    """Verify debiting negative amount raises ValueError."""
    with pytest.raises(ValueError):
        crewed_ship.debit(-5)


def test_debit_insufficient_funds(crewed_ship):
    """Verify debiting more than balance raises InsufficientFundsError."""
    crewed_ship.credit(50)
    with pytest.raises(InsufficientFundsError):
        crewed_ship.debit(100)


def test_best_crew_skill_known(crewed_ship):
    """Verify best crew skill retrieval returns highest crew value."""
    best = crewed_ship.best_crew_skill["Liaison"]
    assert best == 5  # Bob has the highest skill


def test_best_crew_skill_zero(crewed_ship):
    """Verify unknown skill returns zero."""
    best = crewed_ship.best_crew_skill["Tactics"]
    assert best == 0  # None of the crew has this skill


def test_best_crew_skill_case_insensitive(crewed_ship):
    """Verify skill lookup is case-insensitive."""
    best = crewed_ship.best_crew_skill["liAiSON"]
    assert best == 5


def test_can_onload_valid_lot(crewed_ship, setup_gamestate):
    """Verify valid lot passes capacity check."""
    lot = T5Lot("Rhylanor", GameState)
    lot.mass = 10
    assert crewed_ship.can_onload_lot(lot, "freight")


def test_can_onload_rejects_non_t5lot(crewed_ship):
    """Verify non-T5Lot object raises TypeError."""
    with pytest.raises(TypeError, match="Invalid lot type."):
        crewed_ship.can_onload_lot("not_a_lot", "freight")


def test_can_onload_rejects_invalid_lot_type(crewed_ship, setup_gamestate):
    """Verify invalid lot category raises ValueError."""
    lot = T5Lot("Rhylanor", GameState)
    lot.mass = 5
    with pytest.raises(InvalidLotTypeError):
        crewed_ship.can_onload_lot(lot, "contraband")


def test_can_onload_rejects_over_capacity(crewed_ship, setup_gamestate):
    """Verify oversized lot raises ValueError."""
    lot = T5Lot("Rhylanor", GameState)
    lot.mass = 150
    with pytest.raises(CapacityExceededError):
        crewed_ship.can_onload_lot(lot, "cargo")


def test_can_onload_rejects_duplicate_lot(crewed_ship, setup_gamestate):
    """Verify loading same lot twice raises ValueError."""
    lot = T5Lot("Rhylanor", GameState)
    lot.mass = 5
    crewed_ship.cargo["cargo"].append(lot)
    with pytest.raises(DuplicateItemError):
        crewed_ship.can_onload_lot(lot, "cargo")


def test_stateroom_capacity_initialization(test_ship_data, setup_gamestate):
    """Verify ship initializes with correct
    stateroom and low berth capacity."""
    small_class = T5ShipClass("small", test_ship_data["small"])
    small_ship = T5Starship("Tiny", "Rhylanor", small_class)
    assert small_ship.staterooms == 2
    assert small_ship.low_berths == 0

    large_class = T5ShipClass("large", test_ship_data["large"])
    large_ship = T5Starship("Big", "Rhylanor", large_class)
    assert large_ship.staterooms == 10
    assert large_ship.low_berths == 50


def test_high_passenger_capacity_limit(test_ship_data, setup_gamestate):
    """Verify high passengers are limited by stateroom capacity."""
    ship_class = T5ShipClass("small", test_ship_data["small"])
    ship = T5Starship("Overcrowded", "Rhylanor", ship_class)

    # Should be able to board 2 high passengers (2 staterooms)
    passenger1 = T5NPC("High Roller 1")
    passenger2 = T5NPC("High Roller 2")
    ship.onload_passenger(passenger1, "high")
    ship.onload_passenger(passenger2, "high")

    # Third high passenger should fail
    passenger3 = T5NPC("High Roller 3")
    with pytest.raises(CapacityExceededError):
        ship.onload_passenger(passenger3, "high")


def test_mid_passenger_capacity_limit(test_ship_data, setup_gamestate):
    """Verify mid passengers are limited by stateroom capacity."""
    ship_class = T5ShipClass("small", test_ship_data["small"])
    ship = T5Starship("Cramped", "Rhylanor", ship_class)

    # Should be able to board 2 mid passengers
    passenger1 = T5NPC("Mid Traveler 1")
    passenger2 = T5NPC("Mid Traveler 2")
    ship.onload_passenger(passenger1, "mid")
    ship.onload_passenger(passenger2, "mid")

    # Third mid passenger should fail
    passenger3 = T5NPC("Mid Traveler 3")
    with pytest.raises(CapacityExceededError):
        ship.onload_passenger(passenger3, "mid")


def test_get_stateroom_passenger_count(test_ship_data, setup_gamestate):
    """Verify _get_stateroom_passenger_count returns correct count."""
    # Use large ship which has low berths
    ship_class = T5ShipClass("large", test_ship_data["large"])
    ship = T5Starship("TestShip", "Rhylanor", ship_class)

    # Initially should be 0
    assert ship._get_stateroom_passenger_count() == 0

    # Add high passenger
    high_pass = T5NPC("VIP")
    ship.onload_passenger(high_pass, "high")
    assert ship._get_stateroom_passenger_count() == 1

    # Add mid passenger
    mid_pass = T5NPC("Traveler")
    ship.onload_passenger(mid_pass, "mid")
    assert ship._get_stateroom_passenger_count() == 2

    # Low passengers don't count (they use berths, not staterooms)
    low_pass = T5NPC("Budget")
    ship.onload_passenger(low_pass, "low")
    # Still 2, low not counted
    assert ship._get_stateroom_passenger_count() == 2


def test_high_and_mid_passengers_share_staterooms(
        test_ship_data,
        setup_gamestate):
    """Verify high and mid passengers both count against stateroom limit."""
    ship_class = T5ShipClass("small", test_ship_data["small"])
    ship = T5Starship("Mixed", "Rhylanor", ship_class)

    # Board 1 high and 1 mid passenger (uses 2 staterooms)
    high_pass = T5NPC("VIP Guest")
    mid_pass = T5NPC("Regular Traveler")
    ship.onload_passenger(high_pass, "high")
    ship.onload_passenger(mid_pass, "mid")

    # No more staterooms available
    another_high = T5NPC("Another VIP")
    with pytest.raises(CapacityExceededError):
        ship.onload_passenger(another_high, "high")

    another_mid = T5NPC("Another Traveler")
    with pytest.raises(CapacityExceededError):
        ship.onload_passenger(another_mid, "mid")


def test_low_passenger_capacity_limit(test_ship_data, setup_gamestate):
    """Verify low passengers are limited by low berth capacity."""
    ship_class = T5ShipClass("large", test_ship_data["large"])
    ship = T5Starship("Budget Cruiser", "Rhylanor", ship_class)

    # Board 50 low passengers (50 low berths available)
    for i in range(50):
        passenger = T5NPC(f"Low Passenger {i+1}")
        ship.onload_passenger(passenger, "low")

    # 51st should fail
    extra_passenger = T5NPC("One Too Many")
    with pytest.raises(CapacityExceededError):
        ship.onload_passenger(extra_passenger, "low")


def test_low_passengers_independent_of_staterooms(
        test_ship_data,
        setup_gamestate):
    """Verify low passengers don't affect stateroom capacity."""
    ship_class = T5ShipClass("large", test_ship_data["large"])
    ship = T5Starship("Flexible", "Rhylanor", ship_class)

    # Fill all 10 staterooms with high/mid passengers
    for i in range(10):
        passenger = T5NPC(f"Stateroom Guest {i+1}")
        ship.onload_passenger(passenger, "high" if i < 5 else "mid")

    # Should still be able to board low passengers
    low_pass = T5NPC("Budget Traveler")
    ship.onload_passenger(low_pass, "low")
    assert len(ship.passengers["low"]) == 1


def test_ship_with_no_low_berths(test_ship_data, setup_gamestate):
    """Verify ship with no low berths rejects low passengers."""
    ship_class = T5ShipClass("small", test_ship_data["small"])
    ship = T5Starship("No Budget", "Rhylanor", ship_class)

    passenger = T5NPC("Hopeful Budget Traveler")
    with pytest.raises(CapacityExceededError):
        ship.onload_passenger(passenger, "low")


def test_load_passengers(test_ship_data):
    """Test the load_passengers method integrates skills and capacity."""
    from t5code.T5World import T5World

    # Set up world data
    test_world_data = {
        "Rhylanor": {
            "UWP": "A788899-C",
            "TradeClassifications": "Ri",
            "Importance": 4,
        }
    }

    # Create ship with capacity
    ship_class = T5ShipClass("large", test_ship_data["large"])
    ship = T5Starship("Liner", "Rhylanor", ship_class)

    # Add crew with skills
    steward = T5NPC("Chief Steward")
    steward.set_skill("Steward", 3)
    admin = T5NPC("Purser")
    admin.set_skill("Admin", 2)
    fixer = T5NPC("Fixer")
    fixer.set_skill("Streetwise", 4)

    ship.hire_crew("crew1", steward)
    ship.hire_crew("crew2", admin)
    ship.hire_crew("crew3", fixer)

    # Load passengers at a world
    world = T5World("Rhylanor", test_world_data)
    initial_balance = ship.balance
    loaded = ship.load_passengers(world)

    # Verify passengers were loaded
    assert isinstance(loaded, dict)
    assert "high" in loaded and "mid" in loaded and "low" in loaded
    assert loaded["high"] >= 0
    assert loaded["mid"] >= 0
    assert loaded["low"] >= 0

    # Verify passengers are on ship
    total_loaded = loaded["high"] + loaded["mid"] + loaded["low"]
    assert len(ship.passengers["high"]) == loaded["high"]
    assert len(ship.passengers["mid"]) == loaded["mid"]
    assert len(ship.passengers["low"]) == loaded["low"]

    # Verify ship was credited for passengers
    if total_loaded > 0:
        assert ship.balance > initial_balance


def test_load_passengers_exception_handling_high(test_ship_data):
    """Test that ValueError exception is
    caught when loading high passengers."""
    from t5code.T5World import T5World
    from unittest.mock import patch

    test_world_data = {
        "Rhylanor": {
            "UWP": "A788899-C",
            "TradeClassifications": "Ri",
            "Importance": 4,
        }
    }

    ship_class = T5ShipClass("large", test_ship_data["large"])
    ship = T5Starship("Test Ship", "Rhylanor", ship_class)
    ship.staterooms = 10

    steward = T5NPC("Chief Steward")
    steward.set_skill("Steward", 5)
    ship.hire_crew("crew1", steward)

    world = T5World("Rhylanor", test_world_data)

    # Mock onload_passenger to raise ValueError
    # on the 3rd call for high passengers
    original_onload = ship.onload_passenger
    call_count = [0]

    def mock_onload(npc, passage_class):
        if passage_class == "high":
            call_count[0] += 1
            if call_count[0] > 2:
                raise ValueError("Simulated capacity error")
        return original_onload(npc, passage_class)

    with patch.object(world,
                      'high_passenger_availability',
                      return_value=10), \
            patch.object(world,
                         'mid_passenger_availability',
                         return_value=0), \
            patch.object(world,
                         'low_passenger_availability',
                         return_value=0), \
            patch.object(ship,
                         'onload_passenger',
                         side_effect=mock_onload):
        loaded = ship.load_passengers(world)

    # Should have loaded 2 high passengers before ValueError was raised
    assert loaded["high"] == 2
    assert loaded["mid"] == 0
    assert loaded["low"] == 0


def test_load_passengers_exception_handling_mid(test_ship_data):
    """Test that ValueError exception is caught when loading mid passengers."""
    from t5code.T5World import T5World
    from unittest.mock import patch

    test_world_data = {
        "Rhylanor": {
            "UWP": "A788899-C",
            "TradeClassifications": "Ri",
            "Importance": 4,
        }
    }

    ship_class = T5ShipClass("large", test_ship_data["large"])
    ship = T5Starship("Test Ship", "Rhylanor", ship_class)
    ship.staterooms = 10

    admin = T5NPC("Purser")
    admin.set_skill("Admin", 5)
    ship.hire_crew("crew1", admin)

    world = T5World("Rhylanor", test_world_data)

    # Mock onload_passenger to raise ValueError
    # on the 2nd call for mid passengers
    original_onload = ship.onload_passenger
    call_count = [0]

    def mock_onload(npc, passage_class):
        if passage_class == "mid":
            call_count[0] += 1
            if call_count[0] > 1:
                raise ValueError("Simulated capacity error")
        return original_onload(npc, passage_class)

    with patch.object(world,
                      'high_passenger_availability', return_value=0), \
            patch.object(world,
                         'mid_passenger_availability', return_value=10), \
            patch.object(world,
                         'low_passenger_availability', return_value=0), \
            patch.object(ship,
                         'onload_passenger', side_effect=mock_onload):
        loaded = ship.load_passengers(world)

    # Should have loaded 1 mid passenger before ValueError was raised
    assert loaded["high"] == 0
    assert loaded["mid"] == 1
    assert loaded["low"] == 0


def test_load_passengers_exception_handling_low(test_ship_data):
    """Test that ValueError exception is caught when loading low passengers."""
    from t5code.T5World import T5World
    from unittest.mock import patch

    test_world_data = {
        "Rhylanor": {
            "UWP": "A788899-C",
            "TradeClassifications": "Ri",
            "Importance": 4,
        }
    }

    ship_class = T5ShipClass("large", test_ship_data["large"])
    ship = T5Starship("Test Ship", "Rhylanor", ship_class)
    ship.low_berths = 10

    fixer = T5NPC("Fixer")
    fixer.set_skill("Streetwise", 5)
    ship.hire_crew("crew1", fixer)

    world = T5World("Rhylanor", test_world_data)

    # Mock onload_passenger to raise ValueError
    # on the 4th call for low passengers
    original_onload = ship.onload_passenger
    call_count = [0]

    def mock_onload(npc, passage_class):
        if passage_class == "low":
            call_count[0] += 1
            if call_count[0] > 3:
                raise ValueError("Simulated capacity error")
        return original_onload(npc, passage_class)

    with patch.object(world,
                      'high_passenger_availability', return_value=0), \
            patch.object(world,
                         'mid_passenger_availability', return_value=0), \
            patch.object(world,
                         'low_passenger_availability', return_value=20), \
            patch.object(ship,
                         'onload_passenger', side_effect=mock_onload):
        loaded = ship.load_passengers(world)

    # Should have loaded 3 low passengers before ValueError was raised
    assert loaded["high"] == 0
    assert loaded["mid"] == 0
    assert loaded["low"] == 3


def test_sell_cargo_lot_without_trader(test_ship_data, setup_test_gamestate):
    """Test selling cargo lot without trader skill."""
    from t5code.T5Lot import T5Lot
    from unittest.mock import patch

    game_state = setup_test_gamestate
    ship_class = T5ShipClass("large", test_ship_data["large"])
    ship = T5Starship("Trader", "Rhylanor", ship_class)

    # Create and load a cargo lot
    lot = T5Lot("Rhylanor", game_state)
    lot.mass = 5
    ship.credit(lot.origin_value * lot.mass)  # Get funds to buy
    ship.buy_cargo_lot(lot)

    initial_balance = ship.balance

    # Mock the actual value roll to be predictable
    with patch.object(lot, 'consult_actual_value_table', return_value=1.2):
        result = ship.sell_cargo_lot(lot, game_state, use_trader_skill=False)

    # Verify result structure
    assert 'final_amount' in result
    assert 'gross_amount' in result
    assert 'broker_fee' in result
    assert 'profit' in result
    assert 'purchase_cost' in result
    assert 'modifier' in result
    assert 'flux_info' in result

    # flux_info should be None when trader skill not used
    assert result['flux_info'] is None
    assert result['modifier'] == pytest.approx(1.2)

    # Verify lot was removed from cargo
    assert lot not in ship.cargo_manifest["cargo"]

    # Verify balance increased
    assert ship.balance > initial_balance


def test_sell_cargo_lot_with_trader(test_ship_data, setup_test_gamestate):
    """Test selling cargo lot with trader skill."""
    from t5code.T5Lot import T5Lot

    game_state = setup_test_gamestate
    ship_class = T5ShipClass("large", test_ship_data["large"])
    ship = T5Starship("Trader", "Rhylanor", ship_class)

    # Add trader to crew
    trader = T5NPC("Merchant Marcus")
    trader.set_skill("Trader", 3)
    ship.hire_crew("crew1", trader)

    # Create and load a cargo lot
    lot = T5Lot("Rhylanor", game_state)
    lot.mass = 5
    ship.credit(lot.origin_value * lot.mass)
    ship.buy_cargo_lot(lot)

    result = ship.sell_cargo_lot(lot, game_state, use_trader_skill=True)

    # Verify flux_info is present when trader skill used
    assert result['flux_info'] is not None
    assert 'trader_skill' in result['flux_info']
    assert result['flux_info']['trader_skill'] == 3
    assert 'first_die' in result['flux_info']
    assert 'second_die' in result['flux_info']
    assert 'min_multiplier' in result['flux_info']
    assert 'max_multiplier' in result['flux_info']

    # Verify lot was removed
    assert lot not in ship.cargo_manifest["cargo"]


def test_sell_cargo_lot_not_in_hold(test_ship_data, setup_test_gamestate):
    """Test selling cargo lot that's not in hold raises error."""
    from t5code.T5Lot import T5Lot

    game_state = setup_test_gamestate
    ship_class = T5ShipClass("large", test_ship_data["large"])
    ship = T5Starship("Trader", "Rhylanor", ship_class)

    # Create a lot but don't load it
    lot = T5Lot("Rhylanor", game_state)
    lot.mass = 5

    with pytest.raises(ValueError, match="not in cargo hold"):
        ship.sell_cargo_lot(lot, game_state)


def test_buy_cargo_lot(test_ship_data, setup_test_gamestate):
    """Test buying cargo lot debits and loads correctly."""
    from t5code.T5Lot import T5Lot

    game_state = setup_test_gamestate
    ship_class = T5ShipClass("large", test_ship_data["large"])
    ship = T5Starship("Trader", "Rhylanor", ship_class)

    lot = T5Lot("Rhylanor", game_state)
    lot.mass = 5
    cost = lot.origin_value * lot.mass

    # Give ship enough funds
    ship.credit(cost)
    initial_balance = ship.balance
    ship.buy_cargo_lot(lot)

    # Verify balance decreased by cost
    assert ship.balance == initial_balance - cost

    # Verify lot is in cargo
    assert lot in ship.cargo_manifest["cargo"]


def test_buy_cargo_lot_insufficient_funds(
        test_ship_data,
        setup_test_gamestate):
    """Test buying cargo lot with insufficient funds."""
    from t5code.T5Lot import T5Lot

    game_state = setup_test_gamestate
    ship_class = T5ShipClass("large", test_ship_data["large"])
    ship = T5Starship("Trader", "Rhylanor", ship_class)

    # Set balance too low
    ship._balance = 100

    lot = T5Lot("Rhylanor", game_state)
    lot.mass = 500  # Very expensive

    with pytest.raises(InsufficientFundsError):
        ship.buy_cargo_lot(lot)

    # Verify lot is NOT in cargo
    assert lot not in ship.cargo_manifest["cargo"]


def test_buy_cargo_lot_rollback_on_capacity_error(
        test_ship_data,
        setup_test_gamestate):
    """Test that buy_cargo_lot rolls back debit if loading fails."""
    from t5code.T5Lot import T5Lot

    game_state = setup_test_gamestate
    ship_class = T5ShipClass("small", test_ship_data["small"])
    ship = T5Starship("Tiny Trader", "Rhylanor", ship_class)

    lot = T5Lot("Rhylanor", game_state)
    lot.mass = 1000  # Too big for small ship

    # Give ship enough money to buy
    ship.credit(lot.origin_value * lot.mass + 1000000)
    initial_balance = ship.balance

    with pytest.raises(CapacityExceededError):
        ship.buy_cargo_lot(lot)

    # Balance should be unchanged (rolled back)
    assert ship.balance == initial_balance


def test_load_freight_lot(test_ship_data, setup_test_gamestate):
    """Test loading freight lot credits ship correctly."""
    from t5code.T5Lot import T5Lot
    from t5code.T5Tables import FREIGHT_RATE_PER_TON

    game_state = setup_test_gamestate
    ship_class = T5ShipClass("large", test_ship_data["large"])
    ship = T5Starship("Freighter", "Rhylanor", ship_class)

    lot = T5Lot("Rhylanor", game_state)
    lot.mass = 10

    initial_balance = ship.balance
    payment = ship.load_freight_lot(lot)

    # Verify payment amount
    assert payment == FREIGHT_RATE_PER_TON * lot.mass

    # Verify balance increased
    assert ship.balance == initial_balance + payment

    # Verify lot is in freight
    assert lot in ship.cargo_manifest["freight"]


def test_load_freight_lot_no_capacity(test_ship_data, setup_test_gamestate):
    """Test loading freight lot with no capacity raises error."""
    from t5code.T5Lot import T5Lot

    game_state = setup_test_gamestate
    ship_class = T5ShipClass("small", test_ship_data["small"])
    ship = T5Starship("Tiny Ship", "Rhylanor", ship_class)

    lot = T5Lot("Rhylanor", game_state)
    lot.mass = 1000  # Too big

    initial_balance = ship.balance

    with pytest.raises(CapacityExceededError):
        ship.load_freight_lot(lot)

    # Balance should be unchanged
    assert ship.balance == initial_balance


def test_load_mail(test_ship_data, setup_test_gamestate):
    """Test loading mail creates and loads bundle correctly."""
    game_state = setup_test_gamestate
    ship_class = T5ShipClass("large", test_ship_data["large"])
    ship = T5Starship("Courier", "Rhylanor", ship_class)
    ship.set_course_for("Jae Tellona")

    mail_lot = ship.load_mail(game_state, "Jae Tellona")

    # Verify mail bundle created
    assert mail_lot is not None
    assert mail_lot.origin_name == "Rhylanor"
    assert mail_lot.destination_name == "Jae Tellona"

    # Verify mail is on ship
    assert len(ship.mail_bundles) == 1
    assert mail_lot in ship.mail_bundles.values()


def test_sell_cargo_lot_world_not_found(test_ship_data, setup_test_gamestate):
    """Test sell_cargo_lot raises ValueError when world not found."""
    game_state = setup_test_gamestate
    ship_class = T5ShipClass("large", test_ship_data["large"])
    ship = T5Starship("Merchant", "NonExistentWorld", ship_class)

    # Create a cargo lot using valid GameState
    lot = T5Lot("Rhylanor", game_state)
    ship.onload_lot(lot, "cargo")

    # Create a game state with no world data for NonExistentWorld
    class EmptyGameState:
        def __init__(self):
            self.world_data = {}

    empty_game_state = EmptyGameState()

    # Attempt to sell cargo at non-existent world should raise ValueError
    with pytest.raises(WorldNotFoundError):
        ship.sell_cargo_lot(lot, empty_game_state, use_trader_skill=False)


def test_buy_cargo_lot_rollback_preserves_balance(
        test_ship_data,
        setup_test_gamestate):
    """Test buy_cargo_lot rollback on
    capacity error preserves original balance."""
    game_state = setup_test_gamestate
    ship_class = T5ShipClass("large", test_ship_data["large"])
    ship = T5Starship("Merchant", "Rhylanor", ship_class)
    initial_balance = 500000  # Large balance to avoid insufficient funds
    ship.credit(initial_balance)

    # Create a lot
    lot = T5Lot("Rhylanor", game_state)

    # Mock onload_lot to raise CapacityExceededError
    # (simulating capacity error)
    original_onload = ship.onload_lot

    def mock_onload_error(lot, lot_type):
        raise CapacityExceededError(
            required=100,
            available=50,
            capacity_type="cargo hold")

    ship.onload_lot = mock_onload_error

    # Attempt to buy cargo that will fail to load
    # should raise CapacityExceededError
    with pytest.raises(CapacityExceededError):
        ship.buy_cargo_lot(lot)

    # Restore original method
    ship.onload_lot = original_onload

    # Balance should be unchanged (rollback happened)
    assert ship.balance == initial_balance


def test_is_hold_mostly_full_default_threshold(
        test_ship_data,
        setup_test_gamestate):
    """Test is_hold_mostly_full with default 80% threshold."""
    game_state = setup_test_gamestate
    ship_class = T5ShipClass("large", test_ship_data["large"])
    ship = T5Starship("Merchant", "Rhylanor", ship_class)

    # Ship starts empty
    assert ship.is_hold_mostly_full() is False

    # Load cargo to 79% capacity (hold_size = 200)
    from t5code.T5Lot import T5Lot
    lot = T5Lot("Rhylanor", game_state)
    lot.mass = 158  # 79% of 200
    ship.onload_lot(lot, "cargo")
    assert ship.is_hold_mostly_full() is False

    # Load more to reach exactly 80%
    lot2 = T5Lot("Rhylanor", game_state)
    lot2.mass = 2  # Total = 160 = 80% of 200
    ship.onload_lot(lot2, "cargo")
    assert ship.is_hold_mostly_full() is True


def test_is_hold_mostly_full_custom_threshold(
        test_ship_data,
        setup_test_gamestate):
    """Test is_hold_mostly_full with custom threshold."""
    game_state = setup_test_gamestate
    ship_class = T5ShipClass("large", test_ship_data["large"])
    ship = T5Starship("Merchant", "Rhylanor", ship_class)

    # Load to 50% capacity (hold_size = 200)
    from t5code.T5Lot import T5Lot
    lot = T5Lot("Rhylanor", game_state)
    lot.mass = 100
    ship.onload_lot(lot, "cargo")

    # Should be full at 50% threshold
    assert ship.is_hold_mostly_full(threshold=0.5) is True

    # Should not be full at 60% threshold
    assert ship.is_hold_mostly_full(threshold=0.6) is False


def test_is_hold_mostly_full_invalid_threshold(test_ship_data):
    """Test is_hold_mostly_full raises
    InvalidThresholdError for invalid threshold."""
    ship_class = T5ShipClass("large", test_ship_data["large"])
    ship = T5Starship("Merchant", "Rhylanor", ship_class)

    with pytest.raises(InvalidThresholdError):
        ship.is_hold_mostly_full(threshold=-0.1)

    with pytest.raises(InvalidThresholdError):
        ship.is_hold_mostly_full(threshold=1.5)


def test_execute_jump(test_ship_data):
    """Test execute_jump performs correct status transitions."""
    ship_class = T5ShipClass("large", test_ship_data["large"])
    ship = T5Starship("Merchant", "Rhylanor", ship_class)

    # Execute jump to Jae Tellona
    ship.execute_jump("Jae Tellona")

    # Verify final state
    assert ship.location == "Jae Tellona"
    assert ship.destination == "Jae Tellona"
    assert ship.status == "docked"


def test_execute_jump_updates_location(test_ship_data):
    """Test execute_jump updates location correctly."""
    ship_class = T5ShipClass("large", test_ship_data["large"])
    ship = T5Starship("Merchant", "Rhylanor", ship_class)

    initial_location = ship.location
    assert initial_location == "Rhylanor"

    ship.execute_jump("Mora")

    # Location should have changed
    assert ship.location == "Mora"
    assert ship.location != initial_location


def test_offload_all_freight_empty_hold(test_ship_data):
    """Test offload_all_freight with no freight on board."""
    ship_class = T5ShipClass("large", test_ship_data["large"])
    ship = T5Starship("Merchant", "Rhylanor", ship_class)

    offloaded = ship.offload_all_freight()

    assert len(offloaded) == 0
    assert len(list(ship.cargo_manifest.get("freight", []))) == 0


def test_offload_all_freight_with_lots(test_ship_data, setup_test_gamestate):
    """Test offload_all_freight removes all freight."""
    game_state = setup_test_gamestate
    ship_class = T5ShipClass("large", test_ship_data["large"])
    ship = T5Starship("Merchant", "Rhylanor", ship_class)

    # Load multiple freight lots
    from t5code.T5Lot import T5Lot
    lot1 = T5Lot("Rhylanor", game_state)
    lot1.mass = 10
    lot2 = T5Lot("Rhylanor", game_state)
    lot2.mass = 20
    lot3 = T5Lot("Rhylanor", game_state)
    lot3.mass = 15

    ship.onload_lot(lot1, "freight")
    ship.onload_lot(lot2, "freight")
    ship.onload_lot(lot3, "freight")

    # Verify freight is loaded
    assert len(list(ship.cargo_manifest.get("freight", []))) == 3
    assert ship.cargo_size == 45

    # Offload all freight
    offloaded = ship.offload_all_freight()

    # Verify all freight was offloaded
    assert len(offloaded) == 3
    assert len(list(ship.cargo_manifest.get("freight", []))) == 0
    assert ship.cargo_size == 0

    # Verify returned list contains the correct lots
    assert lot1 in offloaded
    assert lot2 in offloaded
    assert lot3 in offloaded


def test_offload_all_freight_leaves_cargo(
        test_ship_data,
        setup_test_gamestate):
    """Test offload_all_freight only removes freight, not cargo."""
    game_state = setup_test_gamestate
    ship_class = T5ShipClass("large", test_ship_data["large"])
    ship = T5Starship("Merchant", "Rhylanor", ship_class)

    # Load freight and cargo
    from t5code.T5Lot import T5Lot
    freight_lot = T5Lot("Rhylanor", game_state)
    freight_lot.mass = 10
    cargo_lot = T5Lot("Rhylanor", game_state)
    cargo_lot.mass = 5

    ship.onload_lot(freight_lot, "freight")
    ship.onload_lot(cargo_lot, "cargo")

    # Verify both are loaded
    assert len(list(ship.cargo_manifest.get("freight", []))) == 1
    assert len(list(ship.cargo_manifest.get("cargo", []))) == 1
    assert ship.cargo_size == 15

    # Offload all freight
    offloaded = ship.offload_all_freight()

    # Verify only freight was offloaded
    assert len(offloaded) == 1
    assert len(list(ship.cargo_manifest.get("freight", []))) == 0
    assert len(list(ship.cargo_manifest.get("cargo", []))) == 1
    assert ship.cargo_size == 5


def test_get_worlds_in_jump_range(setup_test_gamestate, test_ship_data):
    """Test finding worlds within ship's jump range."""
    game_state = setup_test_gamestate

    # Create ship with Jump-3 drive at Rhylanor
    # (Jump-1 wouldn't reach any worlds in test map)
    ship_class = T5ShipClass("large", test_ship_data["large"])
    ship = T5Starship("Test Ship", "Rhylanor", ship_class)

    # Get worlds in range
    reachable = ship.get_worlds_in_jump_range(game_state)

    # Should return a list of world names
    assert isinstance(reachable, list)
    assert len(reachable) > 0

    # Current location should not be in the list
    assert "Rhylanor" not in reachable

    # All returned worlds should exist in world_data
    for world_name in reachable:
        assert world_name in game_state.world_data


def test_get_worlds_in_jump_range_different_ratings(setup_test_gamestate,
                                                    test_ship_data):
    """Test that higher jump rating returns more worlds."""
    game_state = setup_test_gamestate

    # Create ships with different jump ratings
    small_ship_class = T5ShipClass("small", test_ship_data["small"])  # Jump-1
    large_ship_class = T5ShipClass("large", test_ship_data["large"])  # Jump-3

    small_ship = T5Starship("Small Ship", "Rhylanor", small_ship_class)
    large_ship = T5Starship("Large Ship", "Rhylanor", large_ship_class)

    # Get reachable worlds for each ship
    small_ship_range = small_ship.get_worlds_in_jump_range(game_state)
    large_ship_range = large_ship.get_worlds_in_jump_range(game_state)

    # Ship with higher jump rating should reach at least as many worlds
    assert len(large_ship_range) >= len(small_ship_range)

    # All worlds reachable by Jump-1 should also be reachable by Jump-3
    for world in small_ship_range:
        assert world in large_ship_range


def test_get_worlds_in_jump_range_invalid_location(setup_test_gamestate,
                                                   test_ship_data):
    """Test error handling when ship is at invalid location."""
    game_state = setup_test_gamestate
    ship_class = T5ShipClass("small", test_ship_data["small"])
    ship = T5Starship("Test Ship", "NonexistentWorld", ship_class)

    # Should raise WorldNotFoundError
    with pytest.raises(WorldNotFoundError):
        ship.get_worlds_in_jump_range(game_state)


def test_find_profitable_destinations(setup_test_gamestate, test_ship_data):
    """Test finding profitable trade destinations."""
    game_state = setup_test_gamestate

    # Create ship with Jump-3 at Rhylanor
    ship_class = T5ShipClass("large", test_ship_data["large"])
    ship = T5Starship("Test Ship", "Rhylanor", ship_class)
    ship.set_course_for("Jae Tellona")  # Set a destination

    # Get profitable destinations
    profitable = ship.find_profitable_destinations(game_state)

    # Should return a list of (world_name, profit) tuples
    assert isinstance(profitable, list)

    # Each entry should be a tuple of (str, int)
    for entry in profitable:
        assert isinstance(entry, tuple)
        assert len(entry) == 2
        world_name, profit = entry
        assert isinstance(world_name, str)
        assert isinstance(profit, int)
        assert profit > 0  # Should only include profitable destinations
        assert world_name in game_state.world_data

    # Should be sorted by profit descending
    if len(profitable) > 1:
        for i in range(len(profitable) - 1):
            assert profitable[i][1] >= profitable[i+1][1]


def test_find_profitable_destinations_no_worlds_in_range(setup_test_gamestate,
                                                         test_ship_data):
    """Test profitable destinations when no worlds are in range."""
    game_state = setup_test_gamestate

    # Create ship with Jump-0 (no range)
    zero_jump_data = test_ship_data["small"].copy()
    zero_jump_data["jump_rating"] = 0
    ship_class = T5ShipClass("zero_jump", zero_jump_data)
    ship = T5Starship("Test Ship", "Rhylanor", ship_class)

    # Should return empty list
    profitable = ship.find_profitable_destinations(game_state)
    assert profitable == []


def test_find_profitable_destinations_invalid_location(setup_test_gamestate,
                                                       test_ship_data):
    """Test error handling when ship is at invalid location."""
    game_state = setup_test_gamestate
    ship_class = T5ShipClass("small", test_ship_data["small"])
    ship = T5Starship("Test Ship", "NonexistentWorld", ship_class)

    # Should raise WorldNotFoundError
    with pytest.raises(WorldNotFoundError):
        ship.find_profitable_destinations(game_state)


def test_crew_position_clear(test_ship_data, setup_gamestate):
    """Test clearing a crew position."""
    # Add crew positions to ship data
    ship_data_with_crew = test_ship_data["small"].copy()
    # Pilot, Astrogator, Engineer
    ship_data_with_crew["crew_positions"] = ["P", "A", "E"]

    ship_class = T5ShipClass("small", ship_data_with_crew)
    ship = T5Starship("Test Ship", "Rhylanor", ship_class)

    # Get a crew position
    pilot_position = ship.crew_position["Pilot"][0]

    # Assign an NPC
    npc = T5NPC("Test Pilot")
    pilot_position.assign(npc)
    assert pilot_position.is_filled()

    # Clear the position
    pilot_position.clear()
    assert not pilot_position.is_filled()
    assert pilot_position.npc is None


def test_crew_position_repr(test_ship_data, setup_gamestate):
    """Test CrewPosition __repr__ method."""
    ship_data_with_crew = test_ship_data["small"].copy()
    ship_data_with_crew["crew_positions"] = ["P", "A"]

    ship_class = T5ShipClass("small", ship_data_with_crew)
    ship = T5Starship("Test Ship", "Rhylanor", ship_class)

    # Test vacant position repr
    pilot_position = ship.crew_position["Pilot"][0]
    repr_str = repr(pilot_position)
    assert "CrewPosition" in repr_str
    assert "Pilot" in repr_str
    assert "vacant" in repr_str

    # Test filled position repr
    npc = T5NPC("Test Pilot")
    pilot_position.assign(npc)
    repr_str = repr(pilot_position)
    assert "CrewPosition" in repr_str
    assert "Pilot" in repr_str
    assert "filled by Test Pilot" in repr_str
