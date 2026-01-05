"""Starship state machine for discrete-event simulation.

Defines the 12-state finite state machine that merchant starships
follow during trading operations between worlds. Each state has a
duration and specific game actions, creating a realistic trading
cycle.

The state machine was extracted from the sequential GameDriver.py
main() function and formalized for discrete-event simulation,
enabling parallel execution of multiple independent ships.

State Categories:
    - Arrival (3 states): MANEUVERING_TO_PORT -> ARRIVING -> DOCKED
    - Business (5 states): OFFLOADING -> SELLING_CARGO ->
                          LOADING_FREIGHT -> LOADING_CARGO ->
                          LOADING_MAIL -> LOADING_PASSENGERS
    - Departure (2 states): DEPARTING -> MANEUVERING_TO_JUMP
    - Transit (1 state): JUMPING (7 days)

Total cycle duration: ~10.35 days minimum (varies with loading)
"""

from enum import Enum, auto
from typing import Optional, Dict, Any
from dataclasses import dataclass, field


class StarshipState(Enum):
    """States a merchant starship goes through during trading.

    12-state finite state machine representing the complete cycle
    of merchant trading operations. Each state represents a
    distinct phase with specific duration and actions.

    State values use auto() for automatic enumeration. The order
    is logical (grouped by category) but not sequential; actual
    transitions are defined in STATE_TRANSITIONS dict.
    """

    # At origin/current location
    DOCKED = auto()  # Ship at starport, can do business
    OFFLOADING = auto()  # Unloading passengers, mail, freight
    SELLING_CARGO = auto()  # Selling speculative cargo
    LOADING_FREIGHT = auto()  # Loading freight lots (multi-day search)
    LOADING_CARGO = auto()  # Buying speculative cargo
    LOADING_MAIL = auto()  # Loading mail bundles
    LOADING_PASSENGERS = auto()  # Boarding passengers

    # Departure sequence
    DEPARTING = auto()  # Ready to leave, final checks
    MANEUVERING_TO_JUMP = auto()  # Travel from starport to 100D limit

    # In transit
    JUMPING = auto()  # In jump space (7 days)

    # Arrival sequence
    MANEUVERING_TO_PORT = auto()  # Travel from emergence point to starport
    ARRIVING = auto()  # Arrival procedures, ready to dock


@dataclass
class StarshipStateData:
    """Data associated with each state for simulation.

    Captures state information and context for logging, analysis,
    or extended state machine implementations. Currently not used
    by the basic simulation but provided for future extensions.

    Attributes:
        state: The StarshipState enum value
        duration_days: Time spent in this state (fractional)
        location: Current world name (optional)
        destination: Target world name (optional)
        metadata: Additional state-specific data (flexible dict)
    """

    state: StarshipState
    duration_days: float = 0.0  # Time spent in this state
    location: Optional[str] = None  # Current world
    destination: Optional[str] = None  # Target world
    # State-specific data
    metadata: Dict[str, Any] = field(default_factory=dict)


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
    StarshipState.DOCKED: 0.0,  # Instant transition
    StarshipState.OFFLOADING: 0.25,  # 6 hours
    StarshipState.SELLING_CARGO: 0.5,  # 12 hours (broker negotiations)
    StarshipState.LOADING_FREIGHT: 1.0,  # 1 day per freight loading cycle
    StarshipState.LOADING_CARGO: 0.5,  # 12 hours (market shopping)
    StarshipState.LOADING_MAIL: 0.1,  # 2-3 hours (paperwork)
    StarshipState.LOADING_PASSENGERS: 0.25,  # 6 hours (boarding)
    StarshipState.DEPARTING: 0.1,  # 2-3 hours (final checks)
    StarshipState.MANEUVERING_TO_JUMP: 0.5,  # 12 hours (travel to 100D)
    StarshipState.JUMPING: 7.0,  # 7 days in jump space (168 hours)
    StarshipState.MANEUVERING_TO_PORT: 0.5,  # 12 hours (100D to starport)
    StarshipState.ARRIVING: 0.1,  # 2-3 hours (arrival procedures)
}


def get_next_state(current_state: StarshipState) -> (
        Optional[StarshipState]):
    """Get the default next state for a given current state.

    Looks up the current state in STATE_TRANSITIONS and returns
    the first (and typically only) valid next state. Returns None
    if no transition is defined, indicating end of state machine.

    Args:
        current_state: The starship's current state

    Returns:
        The next state in the sequence, or None if no valid
        transition exists

    Note:
        Most states have exactly one next state (linear sequence).
        DOCKED can transition to either OFFLOADING or
        LOADING_FREIGHT depending on whether cargo exists, but
        this function always returns OFFLOADING. Agents handle
        special logic separately.
    """
    transitions = STATE_TRANSITIONS.get(current_state, [])
    return transitions[0] if transitions else None


def get_state_duration(state: StarshipState) -> float:
    """Get the typical duration for a state in days.

    Returns the standard duration from STATE_DURATIONS dict.
    Fractional days represent hours (e.g., 0.25 = 6 hours).

    Args:
        state: The starship state

    Returns:
        Duration in days (fractional for hours). Returns 0.0 if
        state not found in dict (instant transition).

    Example Durations:
        - JUMPING: 7.0 days (168 hours in jump space)
        - LOADING_FREIGHT: 1.0 day (per attempt)
        - OFFLOADING: 0.25 days (6 hours)
        - DOCKED: 0.0 days (instant)
    """
    return STATE_DURATIONS.get(state, 0.0)


def describe_state(state: StarshipState) -> str:
    """Get a human-readable description of state actions.

    Returns a plain-English description of what occurs during
    this state, suitable for logging, debugging, or user display.

    Args:
        state: The starship state

    Returns:
        Description string, or "Unknown state" if state not
        found in descriptions dict

    Example:
        >>> describe_state(StarshipState.LOADING_CARGO)
        'Purchasing speculative cargo'
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
    """Print a summary of all states in a trading voyage.

    Outputs formatted table showing each state in the
    TRADING_VOYAGE_CYCLE with its duration and description.
    Calculates and displays total one-way and round-trip times.

    Useful for understanding the state machine structure and
    validating durations. Can be run directly via:
        python -m t5sim.starship_states

    Output Format:
        STATE_NAME........................ X.XX days
          Human-readable description

    Side Effects:
        Prints formatted output to stdout
    """
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
