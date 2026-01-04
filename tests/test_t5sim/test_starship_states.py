"""Test starship state machine."""

import pytest
from t5sim import (
    StarshipState,
    StarshipStateData,
    get_next_state,
    get_state_duration,
    describe_state,
    TRADING_VOYAGE_CYCLE,
)


def test_state_enum():
    """Test that all states are defined."""
    assert StarshipState.DOCKED
    assert StarshipState.JUMPING
    assert StarshipState.LOADING_CARGO


def test_state_data_creation():
    """Test creating state data."""
    data = StarshipStateData(
        state=StarshipState.DOCKED,
        duration_days=0.5,
        location="Regina",
        destination="Efate",
    )

    assert data.state == StarshipState.DOCKED
    assert data.duration_days == pytest.approx(0.5)
    assert data.location == "Regina"
    assert data.destination == "Efate"
    assert data.metadata == {}


def test_get_next_state():
    """Test state transitions."""
    assert get_next_state(StarshipState.DOCKED) == StarshipState.OFFLOADING
    assert (get_next_state(StarshipState.JUMPING)
            == StarshipState.MANEUVERING_TO_PORT)
    assert get_next_state(StarshipState.ARRIVING) == StarshipState.DOCKED


def test_get_state_duration():
    """Test state durations."""
    assert get_state_duration(StarshipState.JUMPING) == pytest.approx(7.0)
    assert get_state_duration(StarshipState.DOCKED) == pytest.approx(0.0)
    assert (get_state_duration(StarshipState.LOADING_FREIGHT)
            == pytest.approx(1.0))


def test_describe_state():
    """Test state descriptions."""
    desc = describe_state(StarshipState.JUMPING)
    assert "jump space" in desc.lower()
    assert "7 days" in desc


def test_trading_voyage_cycle():
    """Test that voyage cycle contains all expected states."""
    assert len(TRADING_VOYAGE_CYCLE) == 12
    assert StarshipState.DOCKED in TRADING_VOYAGE_CYCLE
    assert StarshipState.JUMPING in TRADING_VOYAGE_CYCLE
    assert TRADING_VOYAGE_CYCLE[0] == StarshipState.MANEUVERING_TO_PORT


def test_voyage_cycle_total_time():
    """Test that voyage cycle time adds up correctly."""
    total = sum(get_state_duration(state) for state in TRADING_VOYAGE_CYCLE)
    # Should be around 10.8 days (reduced from 12.8)
    assert 10.0 < total < 11.0


def test_print_voyage_summary(capsys):
    """Test the print_voyage_summary function."""
    from t5sim.starship_states import print_voyage_summary

    print_voyage_summary()
    captured = capsys.readouterr()

    assert "MERCHANT STARSHIP TRADING VOYAGE" in captured.out
    assert "Total voyage time" in captured.out
    assert "Round trip" in captured.out


def test_main_block():
    """Test running the module as __main__."""
    import subprocess
    import sys

    # Run the module as a script
    result = subprocess.run(
        [sys.executable, "-m", "t5sim.starship_states"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert "MERCHANT STARSHIP TRADING VOYAGE" in result.stdout
    assert "Total voyage time" in result.stdout
