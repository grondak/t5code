"""SimPy agent for merchant starship behavior.

Implements a SimPy process that uses t5code mechanics and the
starship state machine to simulate intelligent trading operations.
The agent implements a 13-state finite state machine representing
the complete cycle of merchant trading between worlds.

State Machine:
    - Arrival: MANEUVERING_TO_PORT -> ARRIVING -> DOCKED
    - Business: OFFLOADING -> SELLING_CARGO -> LOADING_FREIGHT ->
                LOADING_CARGO -> LOADING_MAIL -> LOADING_PASSENGERS ->
                LOADING_FUEL
    - Departure: DEPARTING -> MANEUVERING_TO_JUMP -> JUMPING

Trading Strategy:
    - Analyzes profitable trade routes before jumping
    - Only purchases cargo profitable at destination
    - Waits for minimum hold capacity before departing
    - Uses crew skills for broker negotiations and liaison work
    - Refuels before departure (Cr500/ton)
"""

from typing import TYPE_CHECKING
import simpy
from t5code import (
    T5Starship,
    T5NPC,
    InsufficientFundsError,
    CapacityExceededError,
    WorldNotFoundError
)
from t5code.T5Basics import TravellerCalendar
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

        # Show company balance if ship has an owner
        balance_str = (
            f"company=Cr{self.ship.owner.balance:,.0f}"
            if self.ship.owner
            else f"balance=Cr{self.ship.balance:,.0f}"
        )

        # Extract fuel status
        jump_fuel_current = self.ship.jump_fuel
        jump_fuel_max = self.ship.jump_fuel_capacity
        ops_fuel_current = self.ship.ops_fuel
        ops_fuel_max = self.ship.ops_fuel_capacity

        status = (
            f"[{date_str}] {self.ship.ship_name} "
            f"at {location_display} ({display_state.name}): "
            f"{balance_str}, "
            f"hold ({self.ship.cargo_size}t/{self.ship.hold_size}t, "
            f"{cargo_pct:.0f}%), "
            f"fuel (jump {jump_fuel_current}/{jump_fuel_max}t, "
            f"ops {ops_fuel_current}/{ops_fuel_max}t), "
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
        # Check Captain position first, then Pilot (pilot
        # serves as captain on ships without captain)
        captain_position = self.ship.crew_position.get("Captain")
        pilot_position = self.ship.crew_position.get("Pilot")

        if captain_position and captain_position[0].is_filled():
            captain_npc = captain_position[0].npc
        elif pilot_position and pilot_position[0].is_filled():
            captain_npc = pilot_position[0].npc
        else:
            captain_npc = None

        self.minimum_cargo_threshold = (captain_npc.cargo_departure_threshold
                                        if captain_npc else 0.8)
        self.freight_loading_attempts = 0
        self.max_freight_attempts = 4  # Give up after 4 cycles (12 days)
        self.freight_loaded_this_cycle = False  # Track if freight obtained
        self.broke = False  # Ship has insufficient funds for operations
        self.calendar = TravellerCalendar()

        # Report initial status with destination and crew
        dest_display = self._get_world_display_name(self.ship.destination)
        crew_info = self._format_crew_info()

        # Get ship cost from ship class data
        ship_cost_mcr = 0.0
        ship_class_data = self.simulation.game_state.ship_classes.get(
            self.ship.ship_class
        )
        if ship_class_data:
            ship_cost_mcr = ship_class_data.get("ship_cost", 0.0)

        # Build company info if ship has an owner
        company_info = ""
        if self.ship.owner:
            company_info = (f"  Company: {self.ship.owner.name}, "
                            f"balance: Cr{self.ship.owner.balance:,.0f}\n")

        self._report_status(context=f"{self.ship.ship_name} "
                            f"({self.ship.ship_class}) starting simulation, "
                            f"cost: MCr{ship_cost_mcr}, "
                            f"destination: {dest_display}\n"
                            f"{company_info}"
                            f"  Crew: {crew_info}")

        # Start the agent's processes
        self.process = env.process(self.run())
        self.payroll_process = env.process(self.run_payroll())

    def _build_crew_skills_list(
        self, npc: T5NPC, position_name: str, is_captain: bool = False
    ) -> list[str]:
        """Build list of skill strings for a crew member.

        Args:
            npc: The NPC crew member
            position_name: Position name (e.g., "Captain", "Pilot")
            is_captain: Whether this crew member serves as captain

        Returns:
            List of skill strings (e.g., ["80%", "Pilot-2"])
        """
        skills = []
        if position_name == "Captain" or is_captain:
            # Show captain's risk threshold if they have one
            if hasattr(npc, 'cargo_departure_threshold'):
                threshold_pct = int(npc.cargo_departure_threshold * 100)
                skills.append(f"{threshold_pct}%")

        # Add any skills this NPC has
        for skill_name, skill_level in npc.skills.items():
            # Capitalize skill name for display
            display_name = skill_name.title()
            skills.append(f"{display_name}-{skill_level}")

        return skills

    def _format_crew_member(
        self,
        position_name: str,
        position_index: int,
        position_count: int,
        npc: T5NPC,
        is_captain: bool = False
    ) -> str:
        """Format a single crew member for display.

        Args:
            position_name: Position name (e.g., "Engineer")
            position_index: Index in position list (0-based)
            position_count: Total positions of this type
            npc: The NPC crew member
            is_captain: Whether this crew member serves as captain

        Returns:
            Formatted crew member string (e.g., "Engineer 1: Engineer-3")
        """
        # Determine display name - show "Captain"
        # for pilot who serves as captain
        if is_captain and position_name == "Pilot":
            display_name = "Captain"
        else:
            display_name = (f"{position_name} {position_index + 1}"
                            if position_count > 1
                            else position_name)

        # Build skills list
        skills = self._build_crew_skills_list(npc, position_name, is_captain)

        # Format with or without skills
        if skills:
            return f"{display_name}: {' '.join(skills)}"
        return display_name

    def _format_crew_info(self) -> str:
        """Format crew roster with NPC names and skills for display.

        Returns:
            Comma-separated list of crew members from crew_position.
            Shows position name (or name + number for multiples).
            Captain shows risk threshold percentage.
            On ships without Captain, Pilot is shown as Captain.

        Example:
            "Captain: 80% Pilot-2, Astrogator, Engineer 1, Engineer 2"
        """
        # Check if ship has explicit captain
        has_captain = "Captain" in self.ship.crew_position

        crew_list = []
        for position_name, position_list in self.ship.crew_position.items():
            for i, crew_position in enumerate(position_list):
                if crew_position.is_filled():
                    # First pilot serves as captain on ships without captain
                    is_captain = (not has_captain and
                                  position_name == "Pilot" and i == 0)
                    crew_member = self._format_crew_member(
                        position_name, i, len(position_list),
                        crew_position.npc, is_captain
                    )
                    crew_list.append(crew_member)

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
            dest_display = self._get_world_display_name(self.ship.destination)
            self._report_status(f"departing starport for {dest_display}",
                                state=old_state)
        elif old_state == StarshipState.MANEUVERING_TO_JUMP:
            dest_display = self._get_world_display_name(self.ship.destination)
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
        # Handle ships with no cargo capacity (like Frigates)
        if self.ship.hold_size == 0:
            return False

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

        Broke ships (insufficient funds) sleep indefinitely instead
        of executing normal operations.

        Yields:
            SimPy timeout for state duration from STATE_DURATIONS,
            or very long timeout (1000 days) for broke ships

        States With Actions:
            - OFFLOADING: Offload passengers, mail, freight
            - SELLING_CARGO: Sell cargo lots with broker skill
            - LOADING_FREIGHT: Load freight if space available
            - LOADING_CARGO: Purchase profitable speculative cargo
            - LOADING_MAIL: Load mail bundles
            - LOADING_PASSENGERS: Board high/mid/low passengers
            - LOADING_FUEL: Refuel jump and ops tanks
            - JUMPING: Execute jump and choose next destination
        """
        # Broke ships sleep for remainder of simulation
        if self.broke:
            yield self.env.timeout(1000)  # Sleep for 1000 days
            return

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
        elif self.state == StarshipState.LOADING_FUEL:
            self._load_fuel()
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
                    self.env.now,
                    lot,
                    self.simulation.game_state,
                    use_trader_skill=True
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
                    payment = self.ship.load_freight_lot(self.env.now, lot)
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
            Delegates to lot.calculate_profit_at() which factors in
            trade codes and market conditions at destination.
        """
        _, _, profit = lot.calculate_profit_at(
            self.ship.destination,
            self.simulation.game_state
        )
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

        self.ship.buy_cargo_lot(self.env.now, lot)
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

        Important: Reserves funds for refueling before buying cargo.
        Won't purchase cargo if ship can't afford upcoming fuel costs.

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

            # Reserve funds for refueling -
            # don't buy cargo we can't afford to haul
            fuel_cost = self._calculate_fuel_cost()
            if self.ship.owner.balance < fuel_cost:
                if self.simulation.verbose:
                    self._report_status(
                        f"skipping cargo purchase,"
                        f"need Cr{fuel_cost:,.0f} for fuel")
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
                self.ship.load_passengers(self.env.now, world)
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

    def _calculate_fuel_needed(self) -> tuple[int, int, int]:
        """Calculate fuel needed for both tanks.

        Returns:
            Tuple of (needed_jump, needed_ops, needed_total)
        """
        needed_jump = self.ship.jump_fuel_capacity - self.ship.jump_fuel
        needed_ops = self.ship.ops_fuel_capacity - self.ship.ops_fuel
        needed_total = needed_jump + needed_ops
        return needed_jump, needed_ops, needed_total

    def _calculate_fuel_cost(self) -> int:
        """Calculate cost to fully refuel both tanks at Cr500/ton.

        Returns:
            Total cost in credits to fill both tanks
        """
        _, _, needed_total = self._calculate_fuel_needed()
        return needed_total * 500

    def _distribute_fuel_to_tanks(self, amount: int, needed_jump: int,
                                  needed_ops: int) -> tuple[int, int]:
        """Distribute purchased fuel to jump and ops tanks.

        Prioritizes jump fuel, then ops fuel.

        Args:
            amount: Total fuel purchased (tons)
            needed_jump: Amount of jump fuel needed
            needed_ops: Amount of ops fuel needed

        Returns:
            Tuple of (jump_added, ops_added) amounts
        """
        jump_added = min(amount, needed_jump) if needed_jump > 0 else 0
        remaining = amount - jump_added
        ops_added = min(remaining, needed_ops) if needed_ops > 0 else 0

        self.ship.jump_fuel += jump_added
        self.ship.ops_fuel += ops_added

        return jump_added, ops_added

    def _report_refuel_success(self, jump_added: int, ops_added: int,
                               cost: int) -> None:
        """Report successful refueling in verbose mode.

        Args:
            jump_added: Tons of jump fuel added
            ops_added: Tons of ops fuel added
            cost: Total cost in credits
        """
        if not self.simulation.verbose:
            return

        self._report_status(
            f"refueled {jump_added}t jump + {ops_added}t ops, "
            f"cost Cr{cost:,.0f}, fuel now {self.ship.jump_fuel}/"
            f"{self.ship.jump_fuel_capacity}t jump, {self.ship.ops_fuel}/"
            f"{self.ship.ops_fuel_capacity}t ops")

    def _report_insufficient_funds(self, needed_total: int) -> None:
        """Report insufficient funds for refueling and mark ship as broke.

        Args:
            needed_total: Total fuel needed in tons

        Side Effects:
            - Sets self.broke = True to suspend operations
            - Reports status in verbose mode
        """
        self._mark_ship_broke(
            f"insufficient funds for fuel (need "
            f"Cr{needed_total * 500:,.0f}, have Cr{self.ship.owner.balance:,})"
        )

    def run_payroll(self):
        """Separate SimPy process for monthly crew payroll.

        Runs independently from the main state machine, processing payroll
        on the first day of each month (Days 002, 030, 058, etc.).
        Crew members are paid 100 Cr each. If the ship cannot afford
        payroll, it becomes broke and suspends operations.

        Yields:
            SimPy timeout events until next payroll date

        Side Effects:
            - Debits ship owner account for crew salaries monthly
            - Sets self.broke = True if insufficient funds
            - Reports payroll in verbose mode
        """
        # Process immediate payroll if starting on first day of month
        total_days = self.simulation.starting_day + self.env.now
        day_of_year = int(((total_days - 1) % 365) + 1)
        current_month = self.calendar.get_month(day_of_year)
        if current_month is not None:
            first_day_of_current_month = (
                self.calendar.get_first_day_of_month(current_month)
            )
            if day_of_year == first_day_of_current_month:
                # Starting on first day of month, process payroll immediately
                self._process_monthly_payroll()

        while True:
            # If ship is broke, sleep indefinitely
            if self.broke:
                yield self.env.timeout(1000)
                continue

            # Calculate days until next month starts
            days_until_next_month = self._calculate_days_until_next_month()

            # Wait until next month
            yield self.env.timeout(days_until_next_month)

            # Process payroll if ship is still operational
            if not self.broke:
                self._process_monthly_payroll()

    def _calculate_days_until_next_month(self) -> float:
        """Calculate simulation days until the next month starts.

        Returns:
            Float number of days until first day of next month
        """
        # Calculate current day of year
        total_days = self.simulation.starting_day + self.env.now
        day_of_year = int(((total_days - 1) % 365) + 1)

        # Get next month start day
        next_month_start = self.calendar.get_next_month_start(day_of_year)

        # Calculate days until next month
        if next_month_start > day_of_year:
            # Next month is still this year
            days_until = next_month_start - day_of_year
        else:
            # Next month is next year (wrap around from Month 13)
            days_until = (365 - day_of_year) + next_month_start

        return float(days_until)

    def calculate_total_payroll(self) -> tuple[int, int]:
        """Calculate total monthly payroll for all crew members.

        Salary is based on skill level required for each position:
        100 Cr per skill level. Positions without skills earn 100 Cr.

        Returns:
            Tuple of (total_payroll, crew_count)

        Raises:
            ValueError: If ship class data not found in game_state.ship_classes

        Example:
            >>> # Ship with Pilot-2, Engineer-3, Steward-3
            >>> total, count = agent.calculate_total_payroll()
            >>> # total = 200 + 300 + 300 = 800, count = 3
        """
        ship_class_data = self.simulation.game_state.ship_classes.get(
            self.ship.ship_class
        )

        if not ship_class_data:
            raise ValueError(
                f"Ship class '{self.ship.ship_class}' not found in "
                f"game_state.ship_classes. Available classes: "
                f"{list(self.simulation.game_state.ship_classes.keys())}"
            )

        return self._calculate_skill_based_payroll(ship_class_data)

    def _calculate_skill_based_payroll(self,
                                       ship_class_data: dict) -> (
                                           tuple[int, int]):
        """Calculate payroll based on skill requirements.

        Args:
            ship_class_data: Dictionary with ship class specifications

        Returns:
            Tuple of (total_payroll, crew_count)
        """
        from t5code import T5ShipClass
        ship_class = T5ShipClass(self.ship.ship_class, ship_class_data)

        total_payroll = 0
        crew_count = 0

        for position_name, position_list in self.ship.crew_position.items():
            for i, crew_position in enumerate(position_list):
                if crew_position.is_filled():
                    crew_count += 1
                    salary = self.simulation.get_crew_salary(
                        position_name, i, ship_class
                    )
                    total_payroll += salary

        return total_payroll, crew_count

    def _process_monthly_payroll(self):
        """Process monthly crew payroll based on skill levels.

        Salary is 100 Cr per skill level required for position.
        Example: Pilot-2 earns 200 Cr, Engineer-3 earns 300 Cr.

        Side Effects:
            - Debits ship owner account for crew salaries
            - Sets self.broke = True if insufficient funds
            - Reports payroll in verbose mode
        """
        # Calculate total payroll
        total_payroll, crew_count = self.calculate_total_payroll()

        if crew_count == 0:
            return

        # Calculate current month for reporting
        total_days = self.simulation.starting_day + self.env.now
        day_of_year = int(((total_days - 1) % 365) + 1)
        current_month = self.calendar.get_month(day_of_year)

        # Check if we can afford payroll
        if self.ship.owner.balance < total_payroll:
            self._mark_ship_broke(
                f"insufficient funds for crew payroll (need "
                f"Cr{total_payroll:,}, have Cr{self.ship.owner.balance:,})"
            )
            return

        # Debit from company account
        self.ship.debit(
            self.env.now,
            total_payroll,
            f"Crew payroll: {crew_count} crew, "
            f"Cr{total_payroll:,} total (Month {current_month})"
        )

        if self.simulation.verbose:
            self._report_status(
                f"paid crew payroll: {crew_count} crew, "
                f"Cr{total_payroll:,} total (Month {current_month})"
            )

    def _mark_ship_broke(self, reason: str):
        """Mark ship as broke and suspend operations.

        Consolidates broke-ship handling for both fuel and payroll failures.

        Args:
            reason: Description of why ship is broke

        Side Effects:
            - Sets self.broke = True to suspend all operations
            - Reports status in verbose mode
        """
        self.broke = True

        if self.simulation.verbose:
            self._report_status(f"{reason}, suspending operations")

    def _load_fuel(self):
        """Refuel jump and operations tanks at Cr500 per ton.

        Calculates needed fuel to fill both tanks, determines affordable
        amount based on ship's account balance (Cr500/ton), and purchases
        the minimum of needed and affordable. Fuel is distributed
        proportionally between jump and ops tanks based on their needs.

        Side Effects:
            - Debits ship account for fuel purchase (Cr500 per ton)
            - Updates ship.jump_fuel and ship.ops_fuel levels
            - Prints refueling summary in verbose mode

        Exceptions:
            Catches and logs exceptions to prevent agent failure.

        Notes:
            - If ship has zero balance, no fuel is purchased
            - If tanks are full, no fuel is purchased
            - Fuel is split between jump/ops tanks proportionally
        """
        try:
            (needed_jump,
             needed_ops,
             needed_total) = self._calculate_fuel_needed()

            # Skip if tanks are already full
            if needed_total == 0:
                if self.simulation.verbose:
                    self._report_status("tanks already full, no refuel needed")
                return

            # Calculate how much we can afford (Cr500/ton)
            affordable = self.ship.owner.balance // 500
            to_purchase = min(needed_total, affordable)

            if to_purchase == 0:
                self._report_insufficient_funds(needed_total)
                return

            # Purchase and distribute fuel
            cost = to_purchase * 500
            self.ship.debit(self.env.now, cost, "Fuel purchase")

            jump_added, ops_added = self._distribute_fuel_to_tanks(
                to_purchase, needed_jump, needed_ops)

            self._report_refuel_success(jump_added, ops_added, cost)

        except Exception as e:
            print(f"{self.ship.ship_name}: Fuel loading error: {e}")

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
            # Calculate distance to destination (if world is known)
            try:
                distance = self.ship.get_distance_to(
                    self.ship.destination,
                    self.simulation.game_state
                )

                # Execute jump and consume fuel
                self.ship.execute_jump(self.ship.destination)
                self.ship.consume_jump_fuel(distance)

                if self.simulation.verbose:
                    print(f"{self.ship.ship_name}: Jumped {distance} hexes, "
                          f"fuel remaining: {self.ship.jump_fuel}/"
                          f"{self.ship.jump_fuel_capacity}t")
            except WorldNotFoundError:
                # For unknown worlds, just execute
                # the jump without fuel consumption
                self.ship.execute_jump(self.ship.destination)
                if self.simulation.verbose:
                    print(f"{self.ship.ship_name}: Jumped to unknown world "
                          f"{self.ship.destination} (fuel not consumed)")

            self.voyage_count += 1

            # Pick new destination (simple: alternate between two worlds)
            # This is where we'd implement smarter route planning
            self._choose_next_destination()

        except Exception as e:
            print(f"{self.ship.ship_name}: Jump error: {e}")

    @staticmethod
    def _report_destination_choice(
        verbose: bool,
        report_callback,
        message: str
    ) -> None:
        """Helper to report destination choice in verbose mode.

        Args:
            verbose: Whether verbose reporting is enabled
            report_callback: Optional callback function for reporting
            message: Message to report
        """
        if verbose and report_callback:
            report_callback(message)

    @staticmethod
    def pick_destination(
        ship: T5Starship,
        game_state,
        verbose: bool = False,
        report_callback=None
    ) -> str:
        """Choose destination for a ship, preferring profitable routes.

        Implements intelligent merchant captain decision-making:
        1. Find worlds in jump range with profitable cargo sales
        2. If profitable destinations exist, randomly choose one
        3. If none profitable, randomly choose any reachable world
        4. If no worlds in range, stay at current location

        Args:
            ship: T5Starship to pick destination for
            game_state: GameState with world data
            verbose: Whether to print status messages
            report_callback: Optional callback(message) for status reporting

        Returns:
            Name of chosen destination world

        Note:
            Enhanced destination selection could weight choices by
            expected profit amount rather than uniform random.
        """
        import random

        # First, try to find profitable destinations
        profitable = ship.find_profitable_destinations(game_state)

        if profitable:
            next_dest, expected_profit = random.choice(profitable)
            StarshipAgent._report_destination_choice(
                verbose,
                report_callback,
                f"picked destination '{next_dest}' because it showed "
                f"cargo profit of +Cr{expected_profit}/ton"
            )
            return next_dest

        # No profitable destinations - fall back to any reachable world
        reachable = ship.get_worlds_in_jump_range(game_state)

        if reachable:
            next_dest = random.choice(reachable)
            StarshipAgent._report_destination_choice(
                verbose,
                report_callback,
                f"picked destination '{next_dest}' randomly because "
                f"no in-range system could buy cargo from "
                f"'{ship.location}' for a profit"
            )
            return next_dest

        # No worlds in range - stay at current location
        StarshipAgent._report_destination_choice(
            verbose,
            report_callback,
            "no worlds in jump range!"
        )
        return ship.location

    def _choose_next_destination(self):
        """Choose next destination and set ship course.

        Wrapper around pick_destination() that sets the ship's course
        and handles verbose reporting via _report_status().

        Side Effects:
            - Sets ship.destination via ship.set_course_for()
            - Prints destination choice rationale in verbose mode
        """
        next_dest = self.pick_destination(
            self.ship,
            self.simulation.game_state,
            verbose=self.simulation.verbose,
            report_callback=self._report_status
        )
        self.ship.set_course_for(next_dest)
