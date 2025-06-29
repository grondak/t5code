import pytest
from t5code.T5Starship import T5Starship, DuplicateItemError
from t5code.T5ShipClass import T5ShipClass
from t5code.T5NPC import T5NPC
from t5code.GameState import *
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
        },
        "large": {
            "class_name": "large",
            "jump_rating": 3,
            "maneuver_rating": 3,
            "cargo_capacity": 200,
        },
    }


@pytest.fixture
def setup_gamestate():
    MAP_FILE = "tests/t5_test_map.txt"
    GameState.world_data = T5World.load_all_worlds(load_and_parse_t5_map(MAP_FILE))


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
    starship = get_me_a_starship("Your mom", "Home", test_ship_data)
    assert starship.shipName == "Your mom"
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
    starship = get_me_a_starship("Your mom", "Home", test_ship_data)
    npc1 = T5NPC("Bob")
    with pytest.raises(ValueError, match="Invalid crew position."):
        starship.hire_crew("a string", npc1)
    with pytest.raises(TypeError, match="Invalid NPC."):
        starship.hire_crew("medic", "a something")
    starship.hire_crew("medic", npc1)
    assert starship.crew == {"medic": npc1}


def test_onload_passenger(test_ship_data):
    starship = get_me_a_starship("Titanic", "Southampton", test_ship_data)
    with pytest.raises(TypeError, match="Invalid passenger type."):
        starship.onload_passenger("a string", "high")
    npc1 = T5NPC("Bob")
    with pytest.raises(ValueError, match="Invalid passenger class."):
        starship.onload_passenger(npc1, "yourmom")
    starship.onload_passenger(npc1, "high")
    assert {npc1} == starship.passengers["high"]
    npc2 = T5NPC("Doug")
    starship.onload_passenger(npc2, "high")
    assert {npc1, npc2} == starship.passengers["high"]
    with pytest.raises(
        DuplicateItemError, match="Cannot load same passenger Bob twice."
    ):
        starship.onload_passenger(npc1, "high")
    assert {npc1, npc2} == starship.passengers["high"]
    assert npc1.location == starship.shipName
    assert npc2.location == starship.shipName


def test_offload_passengers(test_ship_data):
    starship = get_me_a_starship("Pequod", "Nantucket", test_ship_data)
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
    offloadedPassengers = starship.offload_passengers("high")
    assert offloadedPassengers == {npc1, npc2}
    assert starship.passengers["high"] == set()
    assert npc1.location == starship.location
    assert npc2.location == starship.location
    with pytest.raises(ValueError, match="Invalid passenger class."):
        starship.offload_passengers("a something")
    offloadedPassengers = starship.offload_passengers("mid")
    assert offloadedPassengers == {npc3}
    assert starship.passengers["mid"] == set()
    assert npc3.location == starship.location
    npc5 = T5NPC("Bones")
    npc5.set_skill("medic", 45)
    starship.hire_crew("medic", npc5)
    offloadedPassengers = starship.offload_passengers("low")
    assert offloadedPassengers == {npc4}
    assert starship.passengers["low"] == set()
    assert npc4.location == starship.location


def test_set_course_for(test_ship_data, setup_gamestate):
    starship = get_me_a_starship("Steamboat", "Rhylanor", test_ship_data)
    starship.set_course_for("Jae Tellona")
    assert starship.destination() == "Jae Tellona"


def test_onload_mail(test_ship_data, setup_gamestate):
    starship = get_me_a_starship("Steamboat", "Rhylanor", test_ship_data)
    mail = T5Mail("Rhylanor", "Jae Tellona", GameState)
    starship.onload_mail(mail)
    assert starship.get_mail()[mail.serial] == mail
    with pytest.raises(ValueError, match="Starship mail locker size exceeded."):
        for mail_number in range(6):
            mail = T5Mail("Rhylanor", "Jae Tellona", GameState)
            starship.onload_mail(mail)


def test_offload_mail(test_ship_data, setup_gamestate):
    starship = get_me_a_starship("Steamboat", "Rhylanor", test_ship_data)
    mail = T5Mail("Rhylanor", "Jae Tellona", GameState)
    starship.onload_mail(mail)
    starship.offload_mail()
    assert len(starship.get_mail().keys()) == 0
    with pytest.raises(ValueError, match="Starship has no mail to offload."):
        starship.offload_mail()


def test_awaken_passenger(test_ship_data):
    starship = get_me_a_starship("Steamboat", "Rhylanor", test_ship_data)
    npc1 = T5NPC("Bones")
    npc1.set_skill("medic", 3)
    starship.hire_crew("medic", npc1)
    npc2 = T5NPC("Ted")
    starship.onload_passenger(npc2, "low")
    assert starship.awakenLowPassenger(npc2, npc1, roll_override_in=20) is True
    assert npc2.get_state() == "Alive"
    assert starship.awakenLowPassenger(npc2, npc1, roll_override_in=-20) is False
    assert npc2.get_state() == "Dead"


def test_onload_lot(test_ship_data, setup_gamestate):
    starship = get_me_a_starship("Steamboat", "Rhylanor", test_ship_data)
    lot = T5Lot("Rhylanor", GameState)
    lot.mass = 5000  # tons
    with pytest.raises(TypeError, match="Invalid lot type."):
        starship.onload_lot("a string", "cargo")
    with pytest.raises(ValueError, match="Invalid lot value."):
        starship.onload_lot(lot, "your mom")
    with pytest.raises(ValueError, match="Lot will not fit in remaining space."):
        starship.onload_lot(lot, "cargo")
    lot.mass = 5  # tons
    starship.onload_lot(lot, "freight")
    assert lot in starship.get_cargo()["freight"]
    with pytest.raises(ValueError, match="Attempt to load same lot twice."):
        starship.onload_lot(lot, "freight")
    with pytest.raises(ValueError, match="Attempt to load same lot twice."):
        starship.onload_lot(lot, "cargo")
    lot2 = T5Lot("Rhylanor", GameState)
    lot2.mass = 5  # tons
    starship.onload_lot(lot2, "cargo")
    assert lot2 in starship.get_cargo()["cargo"]
    lot3 = T5Lot("Rhylanor", GameState)
    with pytest.raises(ValueError, match="Lot will not fit in remaining space."):
        starship.onload_lot(lot3, "cargo")


def test_offload_lot(test_ship_data, setup_gamestate):
    starship = get_me_a_starship("Steamboat", "Rhylanor", test_ship_data)
    lot = T5Lot("Rhylanor", GameState)
    lot.mass = 5
    starship.onload_lot(lot, "cargo")
    lot2 = T5Lot("Rhylanor", GameState)
    lot2.mass = 5
    starship.onload_lot(lot2, "cargo")
    assert lot in starship.get_cargo()["cargo"]
    with pytest.raises(ValueError, match="Invalid lot serial number."):
        starship.offload_lot("your mom", "cargo")
    with pytest.raises(ValueError, match="Invalid lot value."):
        starship.offload_lot(lot.serial, "your mom")
    with pytest.raises(ValueError, match="Lot not found as specified type."):
        starship.offload_lot(lot.serial, "freight")
    lot3 = starship.offload_lot(lot.serial, "cargo")
    isStillThere = any(
        lotIndex.serial == lot3.serial for lotIndex in starship.get_cargo()["cargo"]
    )
    assert lot.serial == lot3.serial
    assert not isStillThere
    assert len(starship.get_cargo()["cargo"]) == 1


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
    assert crewed_ship.balance == 0.0


def test_credit_valid_amount(crewed_ship):
    crewed_ship.credit(100)
    assert crewed_ship.balance == 100.0


def test_debit_valid_amount(crewed_ship):
    crewed_ship.credit(200)
    crewed_ship.debit(50)
    assert crewed_ship.balance == 150.0


def test_credit_invalid_type(crewed_ship):
    with pytest.raises(TypeError):
        crewed_ship.credit("not money")


def test_debit_invalid_type(crewed_ship):
    with pytest.raises(TypeError):
        crewed_ship.debit(None)


def test_credit_negative_amount(crewed_ship):
    with pytest.raises(ValueError):
        crewed_ship.credit(-10)


def test_debit_negative_amount(crewed_ship):
    with pytest.raises(ValueError):
        crewed_ship.debit(-5)


def test_debit_insufficient_funds(crewed_ship):
    crewed_ship.credit(50)
    with pytest.raises(ValueError):
        crewed_ship.debit(100)


def test_best_crew_skill_known(crewed_ship):
    best = crewed_ship.bestCrewSkill["Liaison"]
    assert best == 5  # Bob has the highest skill


def test_best_crew_skill_zero(crewed_ship):
    best = crewed_ship.bestCrewSkill["Tactics"]
    assert best == 0  # None of the crew has this skill


def test_best_crew_skill_case_insensitive(crewed_ship):
    best = crewed_ship.bestCrewSkill["liAiSON"]
    assert best == 5


def test_can_onload_valid_lot(crewed_ship, setup_gamestate):
    lot = T5Lot("Rhylanor", GameState)
    lot.mass = 10
    assert crewed_ship.can_onload_lot(lot, "freight")


def test_can_onload_rejects_non_T5Lot(crewed_ship):
    with pytest.raises(TypeError, match="Invalid lot type."):
        crewed_ship.can_onload_lot("not_a_lot", "freight")


def test_can_onload_rejects_invalid_lot_type(crewed_ship, setup_gamestate):
    lot = T5Lot("Rhylanor", GameState)
    lot.mass = 5
    with pytest.raises(ValueError, match="Invalid lot value."):
        crewed_ship.can_onload_lot(lot, "contraband")


def test_can_onload_rejects_over_capacity(crewed_ship, setup_gamestate):
    lot = T5Lot("Rhylanor", GameState)
    lot.mass = 150
    with pytest.raises(ValueError, match="Lot will not fit"):
        crewed_ship.can_onload_lot(lot, "cargo")


def test_can_onload_rejects_duplicate_lot(crewed_ship, setup_gamestate):
    lot = T5Lot("Rhylanor", GameState)
    lot.mass = 5
    crewed_ship.cargo["cargo"].append(lot)
    with pytest.raises(ValueError, match="load same lot twice"):
        crewed_ship.can_onload_lot(lot, "cargo")
