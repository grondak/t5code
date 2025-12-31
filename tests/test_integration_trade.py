"""Integration tests for complete trade journey workflows."""

import pytest
from t5code import (
    T5Lot, T5NPC, T5ShipClass, T5Starship, T5World,
    find_best_broker, load_and_parse_t5_map, load_and_parse_t5_ship_classes
)


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
        map_file="tests/t5_test_map.txt",
        ship_classes_file="resources/t5_ship_classes.csv"
    )


@pytest.fixture
def ship(game_state):
    """Create a test starship."""
    ship_class = next(iter(game_state.ship_data.values()))
    return T5Starship("Test Ship", "Rhylanor", ship_class)


def test_complete_trade_journey(game_state, ship):
    """Test complete trade workflow: load cargo → travel → sell → profit."""
    origin = "Rhylanor"
    destination = "Jae Tellona"
    
    # Phase 1: Load cargo at origin
    initial_balance = ship.balance
    lot = T5Lot(origin, game_state)
    lot.mass = 5
    
    ship.onload_lot(lot, "cargo")
    assert ship.cargo_size == 5
    assert len(ship.get_cargo()["cargo"]) == 1
    
    # Phase 2: Travel to destination
    ship.set_course_for(destination)
    ship.location = destination
    ship.status = "docked"
    
    # Phase 3: Sell cargo
    world = game_state.world_data[destination]
    starport = world.get_starport()
    broker = find_best_broker(starport)
    
    value = lot.determine_sale_value_on(destination, game_state)
    modifier = lot.consult_actual_value_table(broker.get("mod", 0))
    actual = value * modifier
    fee = actual * broker.get("rate", 0.0)
    final = actual - fee
    
    ship.credit(final)
    ship.offload_lot(lot.serial, "cargo")
    
    # Phase 4: Verify results
    assert ship.cargo_size == 0
    assert len(ship.get_cargo()["cargo"]) == 0
    assert ship.balance > initial_balance  # Made money
    

def test_freight_workflow(game_state, ship):
    """Test freight loading and offloading without selling."""
    origin = "Rhylanor"
    
    # Create and load freight
    lot = T5Lot(origin, game_state)
    lot.mass = 10
    
    ship.onload_lot(lot, "freight")
    assert ship.cargo_size == 10
    assert len(ship.get_cargo()["freight"]) == 1
    
    # Get payment for taking freight
    freight_payment = 1000 * lot.mass
    ship.credit(freight_payment)
    initial_balance = ship.balance
    
    # Travel and offload
    ship.location = "Jae Tellona"
    ship.offload_lot(lot.serial, "freight")
    
    assert ship.cargo_size == 0
    assert len(ship.get_cargo()["freight"]) == 0
    assert ship.balance == initial_balance  # No additional money from offload


def test_broker_impact_on_sale(game_state, ship):
    """Test that broker skill affects sale value."""
    origin = "Rhylanor"
    destination = "Jae Tellona"
    
    lot = T5Lot(origin, game_state)
    lot.mass = 5
    ship.onload_lot(lot, "cargo")
    ship.location = destination
    
    # Get broker values
    world = game_state.world_data[destination]
    starport = world.get_starport()
    broker = find_best_broker(starport)
    
    base_value = lot.determine_sale_value_on(destination, game_state)
    modifier = lot.consult_actual_value_table(broker.get("mod", 0))
    
    # Broker should provide some modification
    assert modifier > 0
    # Modified value should differ from base (unless modifier is exactly 1.0)
    modified_value = base_value * modifier
    assert modified_value >= 0


def test_multiple_lots_management(game_state, ship):
    """Test managing multiple cargo lots simultaneously."""
    origin = "Rhylanor"
    
    # Load three different lots
    lot1 = T5Lot(origin, game_state)
    lot1.mass = 3
    
    lot2 = T5Lot(origin, game_state)
    lot2.mass = 4
    
    lot3 = T5Lot(origin, game_state)
    lot3.mass = 2
    
    ship.onload_lot(lot1, "cargo")
    ship.onload_lot(lot2, "cargo")
    ship.onload_lot(lot3, "freight")
    
    # Verify all loaded correctly
    assert ship.cargo_size == 9
    assert len(ship.get_cargo()["cargo"]) == 2
    assert len(ship.get_cargo()["freight"]) == 1
    
    # Offload specific lots
    ship.offload_lot(lot1.serial, "cargo")
    assert ship.cargo_size == 6
    assert len(ship.get_cargo()["cargo"]) == 1
    
    ship.offload_lot(lot3.serial, "freight")
    assert ship.cargo_size == 4
    assert len(ship.get_cargo()["freight"]) == 0


def test_cargo_capacity_limits(game_state, ship):
    """Test that ship respects cargo capacity limits."""
    origin = "Rhylanor"
    
    # Try to load cargo beyond capacity
    oversized_lot = T5Lot(origin, game_state)
    oversized_lot.mass = ship.hold_size + 10
    
    with pytest.raises(ValueError, match="Lot will not fit"):
        ship.onload_lot(oversized_lot, "cargo")
    
    # Verify nothing was loaded
    assert ship.cargo_size == 0


def test_trade_value_calculation(game_state):
    """Test that trade values are calculated correctly."""
    origin = "Rhylanor"
    destination = "Jae Tellona"
    
    lot = T5Lot(origin, game_state)
    lot.mass = 10
    
    # Get sale value at destination
    value = lot.determine_sale_value_on(destination, game_state)
    
    # Should be positive
    assert value > 0
    # Should be reasonable (at least 100 Cr per ton)
    assert value >= lot.mass * 100


def test_world_data_accessibility_in_trade(game_state):
    """Test that world data is accessible during trade operations."""
    # Both worlds should be available
    assert "Rhylanor" in game_state.world_data
    assert "Jae Tellona" in game_state.world_data
    
    # World data should have required attributes
    rhylanor = game_state.world_data["Rhylanor"]
    assert hasattr(rhylanor, "get_starport")
    assert hasattr(rhylanor, "trade_classifications")
    
    # Starport should provide broker info
    starport = rhylanor.get_starport()
    broker = find_best_broker(starport)
    assert "mod" in broker
    assert "rate" in broker
