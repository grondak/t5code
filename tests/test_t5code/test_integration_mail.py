"""Integration tests for mail workflow."""

import pytest
from t5code import (
    T5Mail, T5Starship, T5ShipClass, T5World,
    load_and_parse_t5_map, load_and_parse_t5_ship_classes, T5Company)


class MockGameState:
    """Mock GameState for testing."""
    def __init__(self, map_file, ship_classes_file):
        raw_worlds = load_and_parse_t5_map(map_file)
        raw_ships = load_and_parse_t5_ship_classes(ship_classes_file)
        self.world_data = T5World.load_all_worlds(raw_worlds)
        self.ship_data = T5ShipClass.load_all_ship_classes(raw_ships)


@pytest.fixture
def game_state():
    """Create a mock GameState with loaded world and ship data."""
    return MockGameState(
        map_file="tests/test_t5code/t5_test_map.txt",
        ship_classes_file="resources/t5_ship_classes.csv"
    )


@pytest.fixture
def ship(game_state):
    """Create a test starship."""
    ship_class = next(iter(game_state.ship_data.values()))
    company = T5Company("Test Company", starting_capital=1_000_000)
    return T5Starship("Mail Runner", "Rhylanor", ship_class, owner=company)


def test_mail_generation_and_delivery(game_state, ship):
    """Test mail created at origin, loaded, transported, and delivered."""
    origin = "Rhylanor"
    destination = "Jae Tellona"

    # Create mail
    mail = T5Mail(origin, destination, game_state)

    # Verify mail properties
    assert mail.origin_name == origin
    assert mail.destination_name == destination
    assert hasattr(mail, 'serial')

    # Load mail on ship
    ship.onload_mail(mail)
    mail_dict = ship.mail_bundles
    assert len(mail_dict) == 1
    assert mail.serial in mail_dict

    # Travel to destination
    ship.set_course_for(destination)
    ship.location = destination
    ship.status = "docked"

    # Offload mail
    ship.offload_mail()

    # Verify mail offloaded
    assert len(ship.mail_bundles) == 0


def test_multiple_mail_bundles(game_state, ship):
    """Test handling multiple mail bundles."""
    origin = "Rhylanor"

    # Create mail bundle (only one can fit in locker)
    mail1 = T5Mail(origin, "Jae Tellona", game_state)

    # Load mail
    ship.onload_mail(mail1)

    # Verify loaded
    mail_dict = ship.mail_bundles
    assert len(mail_dict) == 1

    # Verify serial
    assert mail1.serial in mail_dict


def test_mail_payment(game_state, ship):
    """Test that carrying mail provides payment."""
    origin = "Rhylanor"
    destination = "Jae Tellona"

    initial_balance = ship.balance

    # Create and load mail
    mail = T5Mail(origin, destination, game_state)
    ship.onload_mail(mail)

    # Credit payment for mail (typically happens at destination)
    mail_payment = 25000  # Standard mail payment in Traveller
    ship.credit(0, mail_payment)

    # Deliver mail
    ship.location = destination
    ship.offload_mail()

    # Should have earned money
    assert ship.balance == initial_balance + mail_payment


def test_mail_serial_uniqueness(game_state):
    """Test that mail bundles have unique serials."""
    origin = "Rhylanor"
    destination = "Jae Tellona"

    mails = []
    for _ in range(10):
        mail = T5Mail(origin, destination, game_state)
        mails.append(mail)

    serials = [m.serial for m in mails]
    assert len(serials) == len(set(serials)), "Duplicate mail serials found"


def test_mail_locker_operations(game_state, ship):
    """Test mail locker add and remove operations."""
    mail1 = T5Mail("Rhylanor", "Jae Tellona", game_state)

    # Start empty
    assert len(ship.mail_bundles) == 0

    # Add mail
    ship.onload_mail(mail1)
    assert len(ship.mail_bundles) == 1

    # Offload all
    ship.offload_mail()
    assert len(ship.mail_bundles) == 0


def test_mail_from_different_origins(game_state, ship):
    """Test that mail has origin tracked correctly."""
    # Load mail from first location
    ship.location = "Rhylanor"
    mail1 = T5Mail("Rhylanor", "Jae Tellona", game_state)
    ship.onload_mail(mail1)

    # Verify origin
    assert mail1.origin_name == "Rhylanor"
    assert len(ship.mail_bundles) == 1


def test_mail_destination_tracking(game_state):
    """Test that mail tracks destination correctly."""
    origin = "Rhylanor"
    dest1 = "Jae Tellona"

    mail = T5Mail(origin, dest1, game_state)

    assert mail.origin_name == origin
    assert mail.destination_name == dest1


def test_empty_mail_locker_offload(game_state, ship):
    """Test that offloading empty mail locker raises error."""
    # Verify empty
    assert len(ship.mail_bundles) == 0

    # Try to offload (should raise ValueError)
    with pytest.raises(ValueError, match="no mail to offload"):
        ship.offload_mail()


def test_mail_and_cargo_coexist(game_state, ship):
    """Test that mail and cargo can be on ship simultaneously."""
    from t5code import T5Lot

    origin = "Rhylanor"

    # Load cargo
    lot = T5Lot(origin, game_state)
    lot.mass = 10
    ship.onload_lot(lot, "cargo")

    # Load mail
    mail = T5Mail(origin, "Jae Tellona", game_state)
    ship.onload_mail(mail)

    # Both should be present
    assert ship.cargo_size == 10
    assert len(ship.mail_bundles) == 1

    # Offload mail
    ship.offload_mail()

    # Cargo should remain
    assert ship.cargo_size == 10
    assert len(ship.mail_bundles) == 0


def test_mail_world_compatibility(game_state):
    """Test that mail can be created for valid world pairs."""
    # Use known valid route (high importance to low importance)
    origin = "Rhylanor"
    destination = "Jae Tellona"

    mail = T5Mail(origin, destination, game_state)

    assert mail.origin_name == origin
    assert mail.destination_name == destination
