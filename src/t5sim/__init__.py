"""T5 Simulation - Discrete-event simulation of merchant starship operations.

This module provides large-scale SimPy-based simulation of Traveller 5 trading
operations using the t5code library for game mechanics.
"""

from t5sim.starship_states import (
    StarshipState,
    StarshipStateData,
    STATE_TRANSITIONS,
    STATE_DURATIONS,
    TRADING_VOYAGE_CYCLE,
    get_next_state,
    get_state_duration,
    describe_state,
)

from t5sim.simulation import Simulation
from t5sim.starship_agent import StarshipAgent

__all__ = [
    # State machine
    "StarshipState",
    "StarshipStateData",
    "STATE_TRANSITIONS",
    "STATE_DURATIONS",
    "TRADING_VOYAGE_CYCLE",
    "get_next_state",
    "get_state_duration",
    "describe_state",
    # Main simulation
    "Simulation",
    "StarshipAgent",
]

__version__ = "0.1.0"
