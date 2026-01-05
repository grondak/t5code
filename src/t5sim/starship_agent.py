"""SimPy agent for merchant starship behavior.

Implements a SimPy process that uses t5code mechanics and the
starship state machine to simulate intelligent trading operations.
The agent implements a 12-state finite state machine representing
the complete cycle of merchant trading between worlds.

State Machine:
    - Arrival: MANEUVERING_TO_PORT -> ARRIVING -> DOCKED
    - Business: OFFLOADING -> SELLING_CARGO -> LOADING_FREIGHT ->
                LOADING_CARGO -> LOADING_MAIL -> LOADING_PASSENGERS
    - Departure: DEPARTING -> MANEUVERING_TO_JUMP -> JUMPING

Trading Strategy:
    - Analyzes profitable trade routes before jumping
    - Only purchases cargo profitable at destination
    - Waits for minimum hold capacity before departing
    - Uses crew skills for broker negotiations and liaison work
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

    def _report_status(self,
                       message: str = "",
                       context: str = "",
                       state: StarshipState = None):
        """Report ship status with optional action message.

        Prints detailed ship status including Traveller date, location,
        state, balance, cargo hold capacity, cargo/freight/passengers,
        and mail. Only outputs when verbose mode is enabled.

        Args:
            message: Optional action message to append after status
            context: Optional context string to print before status
            state: Optional state to display (defaults to current)

        Note:
            During JUMPING state, location displays as "jump space"
            instead of showing ship.location.
        """
        if not self.simulation.verbose:
            return

        if context:
            print(f"\n{context}")

        display_state = state if state is not None else self.state
        cargo_pct = ((self.ship.cargo_size /
                     self.ship.hold_size * 100)
                     if self.ship.hold_size > 0 else 0)

        # Format location with subsector and hex
        # During JUMPING state, ship is in jump space, not at a location
        if display_state == StarshipState.JUMPING:
            location_display = "jump space"
        else:
            world = self.simulation.game_state.world_data.get(
                self.ship.location)
            if world:
                location_display = world.full_name()
            else:
                location_display = self.ship.location

        # Extract values for cleaner formatting
        cargo_lots = len(list(self.ship.cargo_manifest.get('cargo', [])))
        freight_lots = len(list(self.ship.cargo_manifest.get('freight', [])))
        high_pax = len(list(self.ship.passengers['high']))
        mid_pax = len(list(self.ship.passengers['mid']))
        low_pax = len(list(self.ship.passengers['low']))
        mail_count = len(self.ship.mail_bundles)

        # Format Traveller date (DDD-YYYY)
        date_str = self.simulation.format_traveller_date(self.env.now)

        status = (
            f"[{date_str}] {self.ship.ship_name} "
            f"at {location_display} ({display_state.name}): "
            f"balance=Cr{self.ship.balance:,.0f}, "
            f"hold ({self.ship.cargo_size}t/{self.ship.hold_size}t, "
            f"{cargo_pct:.0f}%), "
            f"cargo={cargo_lots} lots, "
            f"freight={freight_lots} lots, "
            f"passengers=({high_pax}H/{mid_pax}M/{low_pax}L), "
            f"mail={mail_count} bundles"
        )

        if message:
            print(f"{status} | {message}")
        else:
            print(status)

    def __init__(
        self,
        env: simpy.Environment,
        ship: T5Starship,
        simulation: "Simulation",
        starting_state: StarshipState = StarshipState.DOCKED,

    ):
        """Initialize starship agent and start SimPy process.

        Creates a new starship agent that will execute the trading
        state machine. Automatically starts the SimPy process via
        env.process(self.run()).

        Args:
            env: SimPy environment for discrete-event simulation
            ship: T5Starship instance to control (from t5code)
            simulation: Parent Simulation for world/game data access
            starting_state: Initial state (default: DOCKED)

        Attributes Set:
            minimum_cargo_threshold: From captain's preferences (default 80%)
            max_freight_attempts: Give up loading after 4 cycles
            freight_loading_attempts: Counter for current port
            freight_loaded_this_cycle: Tracks successful freight loads
        """
        self.env = env
        self.ship = ship
        self.simulation = simulation
        self.state = starting_state
        self.voyage_count = 0
        # Get departure threshold from captain's preferences
        captain = self.ship.crew.get("captain")
        self.minimum_cargo_threshold = (captain.cargo_departure_threshold
                                        if captain else 0.8)
        self.freight_loading_attempts = 0
        self.max_freight_attempts = 4  # Give up after 4 cycles (12 days)
        self.freight_loaded_this_cycle = False  # Track if freight obtained

        # Report initial status with destination and crew
        dest_display = self._get_destination_display()
        crew_info = self._format_crew_info()
        self._report_status(context=f"{self.ship.ship_name} "
                            f"({self.ship.ship_class}) starting simulation, "
                            f"destination: {dest_display}\n  "
                            f"Crew: {crew_info}")

        # Start the agent's process
        self.process = env.process(self.run())

    def _format_crew_info(self) -> str:
        """Format crew roster with NPC names and skills for display.

        Returns:
            Comma-separated list of NPCs with their skills.
            Format: "Name: skill-level, skill-level" per NPC.
            Captain shows risk threshold percentage.

        Example:
            "Captain: 80%, Trader: trader-2,
            Steward: steward-1, Medic: medic-1"
        """
        crew_list = []
        for position, npc in self.ship.crew.items():
            # Build skills list for this NPC
            skills = []
            if position == "captain":
                # Show captain's risk threshold
                threshold_pct = int(npc.cargo_departure_threshold * 100)
                skills.append(f"{threshold_pct}%")

            # Add any skills this NPC has
            for skill_name, skill_level in npc.skills.items():
                skills.append(f"{skill_name}-{skill_level}")

            # Format as "NPC Name: skill1, skill2"
            if skills:
                crew_list.append(f"{npc.character_name}: {' '.join(skills)}")
            else:
                crew_list.append(npc.character_name)

        return ", ".join(crew_list)

    def _get_world_display_name(self, world_name: str) -> str:
        """Get formatted display name for a world.

        Args:
            world_name: World identifier

        Returns:
            Formatted world name with subsector/hex or just the name
        """
        world = self.simulation.game_state.world_data.get(world_name)
        return world.full_name() if world else world_name

    def _get_destination_display(self) -> str:
        """Get formatted display name for current destination.

        Returns:
            Formatted destination name with subsector/hex or just the name
        """
        return self._get_world_display_name(self.ship.destination)

    def _report_transition(self, old_state: StarshipState) -> None:
        """Report status after specific state transitions.

        Provides informative messages for key state transitions when
        verbose mode is enabled. Not all transitions generate output;
        only significant operational milestones are reported.

        Args:
            old_state: The state we just completed

        Reported Transitions:
            - JUMPING: Arrival at destination world
            - OFFLOADING: Completion of cargo/passenger offload
            - SELLING_CARGO: Completion of cargo sales
            - LOADING_PASSENGERS: Ready to depart
            - DEPARTING: Leaving starport for jump point
            - MANEUVERING_TO_JUMP: Entering jump space
            - MANEUVERING_TO_PORT: Docking at starport
            - ARRIVING: Docked and ready for business
        """
        if not self.simulation.verbose:
            return

        if old_state == StarshipState.JUMPING:
            location_name = self._get_world_display_name(self.ship.location)
            self._report_status(f"arrived at {location_name}",
                                state=old_state)
        elif old_state == StarshipState.OFFLOADING:
            self._report_status("offloading complete", state=old_state)
        elif old_state == StarshipState.SELLING_CARGO:
            self._report_status("cargo sales complete", state=old_state)
        elif old_state == StarshipState.LOADING_PASSENGERS:
            self._report_status("loading complete, ready to depart",
                                state=old_state)
        elif old_state == StarshipState.DEPARTING:
            dest_display = self._get_destination_display()
            self._report_status(f"departing starport for {dest_display}",
                                state=old_state)
        elif old_state == StarshipState.MANEUVERING_TO_JUMP:
            dest_display = self._get_destination_display()
            self._report_status(f"entering jump space to {dest_display}",
                                state=old_state)
        elif old_state == StarshipState.MANEUVERING_TO_PORT:
            self._report_status("docking at starport", state=old_state)
        elif old_state == StarshipState.ARRIVING:
            self._report_status("docked and ready for business",
                                state=old_state)

    def _should_continue_freight_loading(self) -> bool:
        """Check if ship should continue loading freight.

        Implements the captain's decision logic: wait for minimum
        cargo threshold (80% full) before departing, but give up
        after max_freight_attempts (4 cycles = 12 days) and proceed
        anyway. Resets counter when threshold reached, max attempts
        exceeded, or freight is successfully loaded (giving hope).

        Returns:
            True if should stay in LOADING_FREIGHT state,
            False to proceed to next state

        Side Effects:
            - Increments freight_loading_attempts counter
            - Resets counter when freight loaded or proceeding
            - Prints status messages in verbose mode
        """
        cargo_fill_ratio = self.ship.cargo_size / self.ship.hold_size

        # Reset counter if we got freight this cycle (hope!)
        if self.freight_loaded_this_cycle:
            self.freight_loading_attempts = 0
            self.freight_loaded_this_cycle = False
        else:
            self.freight_loading_attempts += 1

        if cargo_fill_ratio < self.minimum_cargo_threshold:
            # Check if we should keep trying
            if self.freight_loading_attempts < self.max_freight_attempts:
                # Not enough cargo yet, stay in LOADING_FREIGHT state
                if self.simulation.verbose:
                    complete = (self.freight_loading_attempts /
                                self.max_freight_attempts)
                    self._report_status(
                        f"hold only {cargo_fill_ratio*100:.0f}% full, "
                        f"need {self.minimum_cargo_threshold*100:.0f}% "
                        "(continuing freight loading, "
                        f"attempt {complete})")
                # Don't transition, stay in same state
                return True
            else:
                # Give up and proceed
                if self.simulation.verbose:
                    self._report_status(
                        f"hold only {cargo_fill_ratio*100:.0f}% full, "
                        f"but max attempts reached - departing anyway")

        # Reset counter for next port
        self.freight_loading_attempts = 0
        self.freight_loaded_this_cycle = False
        return False

    def _transition_to_next_state(self) -> bool:
        """Transition to the next state in the state machine.

        Handles special case logic (freight loading threshold) then
        advances to the next state using get_next_state(). Calls
        _report_transition() for status updates.

        Returns:
            True if transition succeeded,
            False if stuck (no valid next state)

        Special Cases:
            - LOADING_FREIGHT: May loop if cargo threshold not met
            - All others: Advance to next state in sequence

        Note:
            If this returns False, the agent's run() loop will
            terminate, effectively parking the ship.
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

        Executes the infinite state machine loop: execute current
        state's action (with duration), then transition to next
        state. Continues until simulation ends or agent gets stuck
        (no valid next state).

        Yields:
            SimPy timeout events for state durations

        Flow:
            1. Execute current state action (_execute_state_action)
            2. Wait for state duration via SimPy timeout
            3. Transition to next state (_transition_to_next_state)
            4. Repeat until duration or failure
        """
        while True:
            yield from self._execute_state_action()

            if not self._transition_to_next_state():
                break

    def _execute_state_action(self):
        """Execute the action for the current state.

        Dispatches to state-specific handler methods based on current
        state, then yields a SimPy timeout for the state's duration.
        Most states have no action (pure delays), but key states
        execute trading operations.

        Yields:
            SimPy timeout for state duration from STATE_DURATIONS

        States With Actions:
            - OFFLOADING: Offload passengers, mail, freight
            - SELLING_CARGO: Sell cargo lots with broker skill
            - LOADING_FREIGHT: Load freight if space available
            - LOADING_CARGO: Purchase profitable speculative cargo
            - LOADING_MAIL: Load mail bundles
            - LOADING_PASSENGERS: Board high/mid/low passengers
            - JUMPING: Execute jump and choose next destination
        """
        duration = get_state_duration(self.state)

        # State-specific logic
        if self.state == StarshipState.OFFLOADING:
            self._offload_cargo()
        elif self.state == StarshipState.SELLING_CARGO:
            self._sell_cargo()
        elif self.state == StarshipState.LOADING_FREIGHT:
            self._load_freight()
        elif self.state == StarshipState.LOADING_CARGO:
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
        """Offload passengers, mail, and freight.

        Processes all three types of cargo in order: passengers
        (all classes), mail bundles, then freight lots. Credits
        are automatically added to ship balance by t5code methods.

        Side Effects:
            - Clears passengers from all three classes
            - Delivers mail bundles and collects payment
            - Offloads all freight lots and collects payment

        Exceptions:
            Catches and logs any exceptions during offload process
            to prevent agent failure.
        """
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
        """Sell all cargo lots using broker skill.

        Iterates through all cargo manifest lots and sells each one
        using the crew's trader skill for bonus DMs. Records each
        transaction in simulation statistics for analysis.

        Side Effects:
            - Sells all cargo lots from manifest
            - Credits added to ship balance automatically
            - Records transactions via simulation.record_cargo_sale
            - Prints status for each sale in verbose mode

        Exceptions:
            Catches and logs any exceptions during sale process
            to prevent agent failure.
        """
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
                    self._report_status(
                        f"sold cargo lot for Cr{result['profit']:,.0f} profit")
            except Exception as e:
                print(f"{self.ship.ship_name}: Sale error: {e}")

    def _load_freight(self):
        """Load freight lots (single attempt per cycle).

        Attempts to load one freight lot if hold space available
        and ship not mostly full. Uses liaison skill to determine
        available freight mass via world.freight_lot_mass().
        Payment credited immediately upon loading.

        This is called multiple times if ship remains in
        LOADING_FREIGHT state waiting for minimum cargo threshold.

        Side Effects:
            - Loads one freight lot if space permits
            - Credits payment to ship balance immediately
            - Sets freight_loaded_this_cycle flag if successful
            - Prints status in verbose mode

        Exceptions:
            Silently catches ValueError and CapacityExceededError
            when hold is full or freight unavailable.
        """
        self.freight_loaded_this_cycle = False
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
                    self.freight_loaded_this_cycle = True  # Got freight!
                    if self.simulation.verbose:
                        self._report_status(
                            f"loaded {freight_mass}t freight lot, "
                            f"income Cr{payment:,.0f}")
        except (ValueError, CapacityExceededError):
            pass  # Hold full or other issue

    def _is_lot_profitable(self, lot) -> tuple[bool, float]:
        """Check if a cargo lot would be profitable at destination.

        Calculates purchase price and compares to projected sale
        value at current destination. Returns profitability flag
        and actual profit/loss amount.

        Args:
            lot: T5Lot instance to evaluate

        Returns:
            Tuple of (is_profitable, profit_amount) where
            is_profitable is True if profit > 0, and
            profit_amount is the Cr profit or loss

        Note:
            Uses lot.determine_sale_value_on() which factors in
            trade codes and market conditions at destination.
        """
        purchase_price = lot.origin_value * lot.mass
        sale_value = lot.determine_sale_value_on(
            self.ship.destination,
            self.simulation.game_state
        )
        profit = sale_value - purchase_price
        return profit > 0, profit

    def _try_purchase_lot(self, lot) -> tuple[bool, int]:
        """Try to purchase a cargo lot if profitable.

        Checks profitability using _is_lot_profitable(), then
        attempts purchase if profitable. Returns purchase status
        and mass for statistics tracking.

        Args:
            lot: T5Lot instance to potentially purchase

        Returns:
            Tuple of (purchased, mass) where:
            - purchased: True if lot was bought, False if skipped
            - mass: Tonnage of lot (0 if not purchased)

        Raises:
            InsufficientFundsError: If ship can't afford the lot
            CapacityExceededError: If ship doesn't have space

        Note:
            Caller should catch exceptions to handle funding/space
            issues gracefully.
        """
        is_profitable, _ = self._is_lot_profitable(lot)

        if not is_profitable:
            return False, 0

        self.ship.buy_cargo_lot(lot)
        return True, lot.mass

    def _format_cargo_loading_message(
        self,
        loaded_count: int,
        loaded_mass: int,
        skipped_count: int
    ) -> str:
        """Format verbose message for cargo loading results.

        Creates human-readable summary of cargo loading activity,
        listing both successful purchases and skipped unprofitable
        lots. Returns empty string if no activity occurred.

        Args:
            loaded_count: Number of lots successfully purchased
            loaded_mass: Total tonnage of loaded cargo
            skipped_count: Number of unprofitable lots skipped

        Returns:
            Formatted message string, or empty string if no lots
            were loaded or skipped

        Example:
            "loaded 3 cargo lot(s), 45t total, skipped 2 unprofitable"
        """
        if loaded_count == 0 and skipped_count == 0:
            return ""

        parts = []
        if loaded_count > 0:
            parts.append(f"loaded {loaded_count} cargo lot(s), "
                         f"{loaded_mass}t total")
        if skipped_count > 0:
            parts.append(f"skipped {skipped_count} unprofitable")

        return ", ".join(parts) if parts else ""

    def _load_cargo(self):
        """Purchase speculative cargo, only if profitable.

        Generates available speculative cargo lots at current world
        and evaluates each for profitability at current destination.
        Only purchases lots that show positive profit potential.
        Stops purchasing when funds exhausted or hold full.

        Uses world.generate_speculative_cargo() to get available
        lots, limited by hold space. Iterates through lots and
        calls _try_purchase_lot() for profitability checks.

        Side Effects:
            - Purchases profitable cargo lots (debits ship balance)
            - Prints summary in verbose mode
            - Stops on InsufficientFundsError or CapacityExceeded

        Exceptions:
            Catches and logs exceptions to prevent agent failure.
        """
        try:
            world = self.simulation.game_state.world_data.get(
                self.ship.location)
            if not world:
                return

            available_space = self.ship.hold_size - self.ship.cargo_size
            if available_space <= 0:
                return

            lots = world.generate_speculative_cargo(
                self.simulation.game_state,
                max_total_tons=available_space,
                max_lot_size=available_space,
            )

            loaded_count = 0
            loaded_mass = 0
            skipped_unprofitable = 0

            for lot in lots:
                try:
                    purchased, mass = self._try_purchase_lot(lot)
                    if purchased:
                        loaded_count += 1
                        loaded_mass += mass
                    else:
                        skipped_unprofitable += 1
                except (InsufficientFundsError, CapacityExceededError):
                    break

            if self.simulation.verbose:
                msg = self._format_cargo_loading_message(
                    loaded_count, loaded_mass, skipped_unprofitable
                )
                if msg:
                    self._report_status(msg)

        except Exception as e:
            print(f"{self.ship.ship_name}: Cargo purchase error: {e}")

    def _load_mail(self):
        """Load mail bundles bound for current destination.

        Loads mail bundles from current world to ship's destination,
        up to mail locker capacity. Mail provides guaranteed income
        (Cr25,000 per bundle for jump-1 worlds) upon delivery.

        Side Effects:
            - Loads mail bundles up to mail_locker_size
            - Prints status in verbose mode if any loaded

        Exceptions:
            Silently catches ValueError when no mail available
            or locker already full.
        """
        try:
            if len(self.ship.mail_bundles) < self.ship.mail_locker_size:
                before_count = len(self.ship.mail_bundles)
                self.ship.load_mail(
                    self.simulation.game_state, self.ship.destination
                )
                after_count = len(self.ship.mail_bundles)
                if self.simulation.verbose and after_count > before_count:
                    loaded = after_count - before_count
                    self._report_status(f"loaded {loaded} mail bundle(s)")
        except ValueError:
            pass  # No mail available or locker full

    def _load_passengers(self):
        """Load passengers in all classes (high/mid/low).

        Loads high, middle, and low passage passengers bound for
        current destination, up to stateroom/low berth capacity.
        Uses world.load_passengers() which handles availability
        rolls and capacity checks.

        Passenger Fares (per parsec):
            - High passage: Cr10,000
            - Middle passage: Cr8,000
            - Low passage: Cr1,000

        Side Effects:
            - Loads passengers in all three classes
            - Credits fares to ship balance immediately
            - Prints summary with total income in verbose mode

        Exceptions:
            Catches and logs exceptions to prevent agent failure.
        """
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
                        self._report_status(
                            f"loaded {loaded_high} high, "
                            f"{loaded_mid} mid, {loaded_low} low passengers, "
                            f"income Cr{income:,.0f}")
        except Exception as e:
            print(f"{self.ship.ship_name}: Passenger loading error: {e}")

    def _execute_jump(self):
        """Execute the jump to destination and pick next target.

        Performs the actual jump to ship's current destination using
        ship.execute_jump(), which handles fuel consumption and
        updates ship location. Increments voyage counter. Then
        chooses next destination using _choose_next_destination().

        Side Effects:
            - Executes jump (consumes fuel, updates location)
            - Increments voyage_count
            - Chooses and sets next destination

        Exceptions:
            Catches and logs exceptions to prevent agent failure.

        Note:
            The actual 7-day transit time is handled by state
            duration, not this method.
        """
        try:
            self.ship.execute_jump(self.ship.destination)
            self.voyage_count += 1

            # Pick new destination (simple: alternate between two worlds)
            # This is where we'd implement smarter route planning
            self._choose_next_destination()

        except Exception as e:
            print(f"{self.ship.ship_name}: Jump error: {e}")

    def _choose_next_destination(self):
        """Choose next destination, preferring profitable routes.

        Implements intelligent merchant captain decision-making:
        1. Find worlds in jump range with profitable cargo sales
        2. If profitable destinations exist, randomly choose one
        3. If none profitable, randomly choose any reachable world
        4. If no worlds in range, stay at current location

        Uses ship.find_profitable_destinations() to identify worlds
        where cargo from current location can be sold for profit.
        This creates realistic merchant behavior seeking profit but
        willing to travel speculatively if needed.

        Side Effects:
            - Sets ship.destination via ship.set_course_for()
            - Prints destination choice rationale in verbose mode

        Note:
            Enhanced destination selection could weight choices by
            expected profit amount rather than uniform random.
        """
        import random

        # First, try to find profitable destinations
        profitable = self.ship.find_profitable_destinations(
            self.simulation.game_state)

        if profitable:
            # Choose randomly from profitable destinations
            # (could be enhanced to weight by profit amount)
            next_dest, expected_profit = random.choice(profitable)
            self.ship.set_course_for(next_dest)
            if self.simulation.verbose:
                self._report_status(
                    f"picked destination '{next_dest}' because it showed "
                    f"cargo profit of +Cr{expected_profit}/ton")
        else:
            # No profitable destinations - fall back to any reachable world
            reachable = self.ship.get_worlds_in_jump_range(
                self.simulation.game_state)

            if reachable:
                next_dest = random.choice(reachable)
                self.ship.set_course_for(next_dest)
                if self.simulation.verbose:
                    self._report_status(
                        f"picked destination '{next_dest}' randomly because "
                        f"no in-range system could buy cargo from "
                        f"'{self.ship.location}' for a profit")
            else:
                # No worlds in range - stay at current location
                # This shouldn't happen with proper map design
                self.ship.set_course_for(self.ship.location)
                if self.simulation.verbose:
                    self._report_status("no worlds in jump range!")
