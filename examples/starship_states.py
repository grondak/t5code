"""Starship state machine for discrete-event simulation.

Defines the states and transitions that a merchant starship goes through
during normal trading operations between worlds.

States extracted from GameDriver.py main() function.
"""

from enum import Enum, auto
from typing import Optional, Dict, Any
from dataclasses import dataclass


class StarshipState(Enum):
    """States a merchant starship goes through during trading operations."""

    # At origin/current location
    DOCKED = auto()                  # Ship at starport, can do business
    OFFLOADING = auto()              # Unloading passengers, mail, freight
    SELLING_CARGO = auto()           # Selling speculative cargo
    LOADING_FREIGHT = auto()         # Loading freight lots (multi-day search)
    LOADING_CARGO = auto()           # Buying speculative cargo
    LOADING_MAIL = auto()            # Loading mail bundles
    LOADING_PASSENGERS = auto()      # Boarding passengers

    # Departure sequence
    DEPARTING = auto()               # Ready to leave, final checks
    MANEUVERING_TO_JUMP = auto()     # Travel from starport to 100D limit

    # In transit
    JUMPING = auto()                 # In jump space (7 days)

    # Arrival sequence
    MANEUVERING_TO_PORT = auto()     # Travel from emergence point to starport
    ARRIVING = auto()                # Arrival procedures, ready to dock


@dataclass
class StarshipStateData:
    """Data associated with each state for simulation."""

    state: StarshipState
    duration_days: float = 0.0       # Time spent in this state
    location: Optional[str] = None   # Current world
    destination: Optional[str] = None  # Target world
    metadata: Dict[str, Any] = None  # State-specific data

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


# State transition map: current_state -> list of possible next states
STATE_TRANSITIONS = {
    StarshipState.ARRIVING: [StarshipState.DOCKED],
    StarshipState.DOCKED: [StarshipState.OFFLOADING,
                           StarshipState.LOADING_FREIGHT],
    StarshipState.OFFLOADING: [StarshipState.SELLING_CARGO],
    StarshipState.SELLING_CARGO: [StarshipState.LOADING_FREIGHT],
    StarshipState.LOADING_FREIGHT: [StarshipState.LOADING_CARGO],
    StarshipState.LOADING_CARGO: [StarshipState.LOADING_MAIL],
    StarshipState.LOADING_MAIL: [StarshipState.LOADING_PASSENGERS],
    StarshipState.LOADING_PASSENGERS: [StarshipState.DEPARTING],
    StarshipState.DEPARTING: [StarshipState.MANEUVERING_TO_JUMP],
    StarshipState.MANEUVERING_TO_JUMP: [StarshipState.JUMPING],
    StarshipState.JUMPING: [StarshipState.MANEUVERING_TO_PORT],
    StarshipState.MANEUVERING_TO_PORT: [StarshipState.ARRIVING],
}


# Typical durations for each state (in days)
# These can be overridden by simulation logic
STATE_DURATIONS = {
    StarshipState.DOCKED: 0.0,               # Instant transition
    StarshipState.OFFLOADING: 0.25,          # 6 hours
    StarshipState.SELLING_CARGO: 0.5,        # 12 hours (broker negotiations)
    StarshipState.LOADING_FREIGHT: 3.0,      # Variable: multi-day search (3d)
    StarshipState.LOADING_CARGO: 0.5,        # 12 hours (market shopping)
    StarshipState.LOADING_MAIL: 0.1,         # 2-3 hours (paperwork)
    StarshipState.LOADING_PASSENGERS: 0.25,  # 6 hours (boarding)
    StarshipState.DEPARTING: 0.1,            # 2-3 hours (final checks)
    StarshipState.MANEUVERING_TO_JUMP: 0.5,  # 12 hours (travel to 100D)
    StarshipState.JUMPING: 7.0,              # 7 days in jump space (168 hours)
    StarshipState.MANEUVERING_TO_PORT: 0.5,  # 12 hours (100D to starport)
    StarshipState.ARRIVING: 0.1,             # 2-3 hours (arrival procedures)
}


def get_next_state(current_state: StarshipState) -> Optional[StarshipState]:
    """Get the default next state for a given current state.

    Args:
        current_state: The starship's current state

    Returns:
        The next state in the sequence, or None if no valid transition
    """
    transitions = STATE_TRANSITIONS.get(current_state, [])
    return transitions[0] if transitions else None


def get_state_duration(state: StarshipState) -> float:
    """Get the typical duration for a state in days.

    Args:
        state: The starship state

    Returns:
        Duration in days (fractional for hours)
    """
    return STATE_DURATIONS.get(state, 0.0)


def describe_state(state: StarshipState) -> str:
    """Get a human-readable description of what happens in this state.

    Args:
        state: The starship state

    Returns:
        Description string
    """
    descriptions = {
        StarshipState.DOCKED: "Ship docked at starport, ready for business",
        StarshipState.OFFLOADING: "Offloading passengers, mail, and freight",
        StarshipState.SELLING_CARGO:
            "Selling speculative cargo through brokers",
        StarshipState.LOADING_FREIGHT:
            "Searching for freight lots (multi-day)",
        StarshipState.LOADING_CARGO: "Purchasing speculative cargo",
        StarshipState.LOADING_MAIL: "Loading mail bundles for delivery",
        StarshipState.LOADING_PASSENGERS: "Boarding high/mid/low passengers",
        StarshipState.DEPARTING: "Final departure checks and clearance",
        StarshipState.MANEUVERING_TO_JUMP:
            "Traveling to jump point (100D limit)",
        StarshipState.JUMPING: "In jump space (7 days transit)",
        StarshipState.MANEUVERING_TO_PORT:
            "Traveling from emergence to starport",
        StarshipState.ARRIVING: "Arrival procedures and docking clearance",
    }
    return descriptions.get(state, "Unknown state")


# Define the complete cycle for a trading voyage
TRADING_VOYAGE_CYCLE = [
    # Arrival
    StarshipState.MANEUVERING_TO_PORT,
    StarshipState.ARRIVING,
    StarshipState.DOCKED,

    # Unload & Sell
    StarshipState.OFFLOADING,
    StarshipState.SELLING_CARGO,

    # Load & Buy
    StarshipState.LOADING_FREIGHT,
    StarshipState.LOADING_CARGO,
    StarshipState.LOADING_MAIL,
    StarshipState.LOADING_PASSENGERS,

    # Departure
    StarshipState.DEPARTING,
    StarshipState.MANEUVERING_TO_JUMP,

    # Transit
    StarshipState.JUMPING,
]


def print_voyage_summary():
    """Print a summary of all states in a trading voyage."""
    print("=" * 70)
    print("MERCHANT STARSHIP TRADING VOYAGE - STATE SEQUENCE")
    print("=" * 70)

    total_time = 0.0
    for state in TRADING_VOYAGE_CYCLE:
        duration = get_state_duration(state)
        total_time += duration

        print(f"\n{state.name:.<30} {duration:>6.2f} days")
        print(f"  {describe_state(state)}")

    print(f"\n{'=' * 70}")
    print(f"Total voyage time (one-way): {total_time:.2f} days")
    print(f"Round trip (two jumps):      {total_time * 2:.2f} days")
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    print_voyage_summary()
