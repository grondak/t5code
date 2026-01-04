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
        verbose: Whether to print detailed status updates
    """

    def _report_ship_status(self, context: str = ""):
        """Report current ship status (similar to GameDriver).

        Args:
            context: Optional context string to print before status
        """
        if not self.simulation.verbose:
            return

        if context:
            print(f"\n{context}")

        print(
            f"[Day {self.env.now:.1f}] {self.ship.ship_name} "
            f"at {self.ship.location} ({self.state.name}): "
            f"balance=Cr{self.ship.balance:,.0f}, "
            f"cargo={len(list(self.ship.cargo_manifest.get('cargo', [])))}"
            "lots "
            f"({self.ship.cargo_size}t), "
            f"freight={len(list(self.ship.cargo_manifest.get('freight', [])))}"
            "lots, "
            f"passengers=({len(list(self.ship.passengers['high']))}H/"
            f"{len(list(self.ship.passengers['mid']))}M/"
            f"{len(list(self.ship.passengers['low']))}L), "
            f"mail={len(self.ship.mail_bundles)} bundles"
        )

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
        # Captain won't depart until 80% full
        self.minimum_cargo_threshold = 0.8
        self.freight_loading_attempts = 0
        self.max_freight_attempts = 4  # Give up after 4 cycles (12 days)

        # Report initial status
        self._report_ship_status(f"{self.ship.ship_name} starting simulation")

        # Start the agent's process
        self.process = env.process(self.run())

    def _report_transition(self, old_state: StarshipState) -> None:
        """Report status after specific state transitions.

        Args:
            old_state: The state we just completed
        """
        if not self.simulation.verbose:
            return

        if old_state == StarshipState.JUMPING:
            self._report_ship_status(
                f"{self.ship.ship_name} arrived at {self.ship.location}")
        elif old_state == StarshipState.OFFLOADING:
            self._report_ship_status(
                f"{self.ship.ship_name} offloading complete")
        elif old_state == StarshipState.SELLING_CARGO and self.speculate_cargo:
            self._report_ship_status(
                f"{self.ship.ship_name} cargo sales complete")
        elif old_state == StarshipState.LOADING_PASSENGERS:
            print(f"  {self.ship.ship_name} loading complete, ready to depart")
        elif old_state == StarshipState.DEPARTING:
            print(f"  {self.ship.ship_name} departing starport")
        elif old_state == StarshipState.MANEUVERING_TO_JUMP:
            print(f"  {self.ship.ship_name} entering jump space")
        elif old_state == StarshipState.MANEUVERING_TO_PORT:
            print(f"  {self.ship.ship_name} docking at starport")
        elif old_state == StarshipState.ARRIVING:
            print(f"  {self.ship.ship_name} docked and ready for business")

    def _should_continue_freight_loading(self) -> bool:
        """Check if ship should continue loading freight.

        Returns:
            True if should stay in LOADING_FREIGHT state, False to proceed
        """
        cargo_fill_ratio = self.ship.cargo_size / self.ship.hold_size
        self.freight_loading_attempts += 1

        if cargo_fill_ratio < self.minimum_cargo_threshold:
            # Check if we should keep trying
            if self.freight_loading_attempts < self.max_freight_attempts:
                # Not enough cargo yet, stay in LOADING_FREIGHT state
                if self.simulation.verbose:
                    complete = (self.freight_loading_attempts /
                                self.max_freight_attempts)
                    print(f"  Hold only {cargo_fill_ratio*100:.0f}% full, "
                          f"need {self.minimum_cargo_threshold*100:.0f}% "
                          "(continuing freight loading, "
                          f"attempt {complete})")
                # Don't transition, stay in same state
                return True
            else:
                # Give up and proceed
                if self.simulation.verbose:
                    print(f"  Hold only {cargo_fill_ratio*100:.0f}% full, "
                          f"but max attempts reached - departing anyway")

        # Reset counter for next port
        self.freight_loading_attempts = 0
        return False

    def _transition_to_next_state(self) -> bool:
        """Transition to the next state in the state machine.

        Returns:
            True if transition succeeded, False if stuck (no valid next state)
        """
        # Special check: after loading freight, verify minimum cargo threshold
        if self.state == StarshipState.LOADING_FREIGHT:
            if self._should_continue_freight_loading():
                return True

        next_state = get_next_state(self.state)
        if not next_state:
            print(f"Warning: {self.ship.ship_name} stuck in {self.state}")
            return False

        old_state = self.state
        self.state = next_state
        self._report_transition(old_state)
        return True

    def run(self):
        """Main SimPy process loop for the starship agent.

        Yields:
            SimPy timeout events for state durations
        """
        while True:
            yield from self._execute_state_action()

            if not self._transition_to_next_state():
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
                if self.simulation.verbose:
                    print("  Sold cargo lot for "
                          f"Cr{result['profit']:,.0f} profit")
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
                    payment = self.ship.load_freight_lot(lot)
                    if self.simulation.verbose:
                        print(f"  Loaded {freight_mass}t freight lot, "
                              f"income Cr{payment:,.0f}")
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
                    loaded_count = 0
                    loaded_mass = 0
                    for lot in lots:
                        try:
                            self.ship.buy_cargo_lot(lot)
                            loaded_count += 1
                            loaded_mass += lot.mass
                        except (InsufficientFundsError, CapacityExceededError):
                            break
                    if self.simulation.verbose and loaded_count > 0:
                        print(f"  Loaded {loaded_count} "
                              f"cargo lot(s), {loaded_mass}t total")
        except Exception as e:
            print(f"{self.ship.ship_name}: Cargo purchase error: {e}")

    def _load_mail(self):
        """Load mail bundles."""
        try:
            if len(self.ship.mail_bundles) < self.ship.mail_locker_size:
                before_count = len(self.ship.mail_bundles)
                self.ship.load_mail(
                    self.simulation.game_state, self.ship.destination
                )
                after_count = len(self.ship.mail_bundles)
                if self.simulation.verbose and after_count > before_count:
                    loaded = after_count - before_count
                    print(f"  Loaded {loaded} mail bundle(s)")
        except ValueError:
            pass  # No mail available or locker full

    def _load_passengers(self):
        """Load passengers."""
        try:
            world = self.simulation.game_state.world_data.get(
                self.ship.location)
            if world:
                before_high = len(self.ship.passengers['high'])
                before_mid = len(self.ship.passengers['mid'])
                before_low = len(self.ship.passengers['low'])
                self.ship.load_passengers(world)
                after_high = len(self.ship.passengers['high'])
                after_mid = len(self.ship.passengers['mid'])
                after_low = len(self.ship.passengers['low'])
                if self.simulation.verbose:
                    loaded_high = after_high - before_high
                    loaded_mid = after_mid - before_mid
                    loaded_low = after_low - before_low
                    if loaded_high + loaded_mid + loaded_low > 0:
                        from t5code.T5Tables import PASSENGER_FARES
                        income = (loaded_high * PASSENGER_FARES['high'] +
                                  loaded_mid * PASSENGER_FARES['mid'] +
                                  loaded_low * PASSENGER_FARES['low'])
                        print(f"  Loaded {loaded_high} high, "
                              f"{loaded_mid} mid, "
                              f"{loaded_low} low passengers, "
                              f"income Cr{income:,.0f}")
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
