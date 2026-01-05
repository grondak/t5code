"""T5 Simulation - Discrete-event merchant starship simulation.

Provides large-scale SimPy-based simulation of Traveller 5 merchant
trading operations. Uses the t5code library for all game mechanics
while implementing discrete-event simulation for scalable multi-ship
operations.

Key Components:
    - Simulation: Main orchestrator managing SimPy environment
    - StarshipAgent: SimPy process implementing trading behavior
    - StarshipState: 12-state finite state machine for trade cycles
    - Comprehensive statistics tracking and reporting

Example:
    >>> from t5sim import Simulation
    >>> from t5code.GameState import GameState
    >>> game_state = GameState()
    >>> sim = Simulation(game_state, num_ships=10, duration_days=365)
    >>> results = sim.run()
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
