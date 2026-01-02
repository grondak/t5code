"""SimPy agent for merchant starship behavior.

Implements a SimPy process that uses t5code mechanics and the starship
state machine to simulate trading operations.
"""

from typing import TYPE_CHECKING
import simpy
from t5code import T5Starship, InsufficientFundsError, CapacityExceededError
from t5sim.starship_states import (
    StarshipState,
    get_next_state,
    get_state_duration,
)

if TYPE_CHECKING:
    from t5sim.simulation import Simulation


class StarshipAgent:
    """SimPy process agent representing a merchant starship.

    Uses the t5code T5Starship class for all game mechanics while
    implementing SimPy process behavior for discrete-event simulation.

    Attributes:
        env: SimPy environment
        ship: T5Starship instance from t5code
        simulation: Parent simulation instance
        state: Current starship state
        voyage_count: Number of completed voyages
    """

    def __init__(
        self,
        env: simpy.Environment,
        ship: T5Starship,
        simulation: "Simulation",
        starting_state: StarshipState = StarshipState.DOCKED,
        speculate_cargo: bool = True,
    ):
        """Initialize starship agent.

        Args:
            env: SimPy environment
            ship: T5Starship instance to control
            simulation: Parent simulation for data access
            starting_state: Initial state (default: DOCKED)
            speculate_cargo: Whether to buy/sell
              speculative cargo (default: True)
        """
        self.env = env
        self.ship = ship
        self.simulation = simulation
        self.state = starting_state
        self.voyage_count = 0
        self.speculate_cargo = speculate_cargo

        # Start the agent's process
        self.process = env.process(self.run())

    def run(self):
        """Main SimPy process loop for the starship agent.

        Yields:
            SimPy timeout events for state durations
        """
        while True:
            # Execute state action
            yield from self._execute_state_action()

            # Transition to next state
            next_state = get_next_state(self.state)
            if next_state:
                self.state = next_state
            else:
                # No valid transition - shouldn't happen
                print(f"Warning: {self.ship.ship_name} stuck in {self.state}")
                break

    def _execute_state_action(self):
        """Execute the action for the current state.

        Yields:
            SimPy timeout for state duration
        """
        duration = get_state_duration(self.state)

        # State-specific logic
        if self.state == StarshipState.OFFLOADING:
            self._offload_cargo()
        elif self.state == StarshipState.SELLING_CARGO:
            if self.speculate_cargo:
                self._sell_cargo()
        elif self.state == StarshipState.LOADING_FREIGHT:
            self._load_freight()
        elif self.state == StarshipState.LOADING_CARGO:
            if self.speculate_cargo:
                self._load_cargo()
        elif self.state == StarshipState.LOADING_MAIL:
            self._load_mail()
        elif self.state == StarshipState.LOADING_PASSENGERS:
            self._load_passengers()
        elif self.state == StarshipState.JUMPING:
            self._execute_jump()

        # Wait for state duration
        yield self.env.timeout(duration)

    def _offload_cargo(self):
        """Offload passengers, mail, and freight."""
        try:
            # Offload passengers
            for passage_class in ["high", "mid", "low"]:
                self.ship.offload_passengers(passage_class)

            # Offload mail
            if len(self.ship.mail_bundles) > 0:
                self.ship.offload_mail()

            # Offload freight
            self.ship.offload_all_freight()

        except Exception as e:
            print(f"{self.ship.ship_name}: Offload error: {e}")

    def _sell_cargo(self):
        """Sell all cargo lots."""
        cargo_lots = list(self.ship.cargo_manifest.get("cargo", []))
        for lot in cargo_lots:
            try:
                result = self.ship.sell_cargo_lot(
                    lot, self.simulation.game_state, use_trader_skill=True
                )
                # Record transaction in simulation statistics
                self.simulation.record_cargo_sale(
                    self.ship.ship_name,
                    self.ship.location,
                    result["profit"],
                )
            except Exception as e:
                print(f"{self.ship.ship_name}: Sale error: {e}")

    def _load_freight(self):
        """Load freight lots (simplified - single attempt)."""
        try:
            world = self.simulation.game_state.world_data.get(
                self.ship.location)
            if world:
                liaison_skill = self.ship.best_crew_skill["Liaison"]
                freight_mass = world.freight_lot_mass(liaison_skill)
                if freight_mass > 0 and not self.ship.is_hold_mostly_full():
                    from t5code import T5Lot

                    lot = T5Lot(self.ship.location, self.simulation.game_state)
                    lot.mass = freight_mass
                    self.ship.load_freight_lot(lot)
        except (ValueError, CapacityExceededError):
            pass  # Hold full or other issue

    def _load_cargo(self):
        """Purchase speculative cargo."""
        try:
            world = self.simulation.game_state.world_data.get(
                self.ship.location)
            if world:
                available_space = self.ship.hold_size - self.ship.cargo_size
                if available_space > 0:
                    lots = world.generate_speculative_cargo(
                        self.simulation.game_state,
                        max_total_tons=available_space,
                        max_lot_size=available_space,
                    )
                    for lot in lots:
                        try:
                            self.ship.buy_cargo_lot(lot)
                        except (InsufficientFundsError, CapacityExceededError):
                            break
        except Exception as e:
            print(f"{self.ship.ship_name}: Cargo purchase error: {e}")

    def _load_mail(self):
        """Load mail bundles."""
        try:
            if len(self.ship.mail_bundles) < self.ship.mail_locker_size:
                self.ship.load_mail(
                    self.simulation.game_state, self.ship.destination
                )
        except ValueError:
            pass  # No mail available or locker full

    def _load_passengers(self):
        """Load passengers."""
        try:
            world = self.simulation.game_state.world_data.get(
                self.ship.location)
            if world:
                self.ship.load_passengers(world)
        except Exception as e:
            print(f"{self.ship.ship_name}: Passenger loading error: {e}")

    def _execute_jump(self):
        """Execute the jump to destination."""
        try:
            self.ship.execute_jump(self.ship.destination)
            self.voyage_count += 1

            # Pick new destination (simple: alternate between two worlds)
            # This is where we'd implement smarter route planning
            self._choose_next_destination()

        except Exception as e:
            print(f"{self.ship.ship_name}: Jump error: {e}")

    def _choose_next_destination(self):
        """Choose next destination world.

        Simple implementation: Pick a random neighboring world.
        TODO: Implement trade route optimization.
        """
        import random

        current = self.ship.location
        all_worlds = list(self.simulation.game_state.world_data.keys())

        # Remove current world
        candidates = [w for w in all_worlds if w != current]

        if candidates:
            next_dest = random.choice(candidates)
            self.ship.set_course_for(next_dest)
