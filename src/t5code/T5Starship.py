"""Starship simulation and cargo/passenger/crew management.

Defines the T5Starship class for simulating starship operations including
passenger and crew management, cargo handling, and financial tracking.
"""

import uuid
from typing import Dict, List, Set, Tuple, TYPE_CHECKING, Optional
from t5code.T5Basics import check_success
from t5code.T5Lot import T5Lot
from t5code.T5NPC import T5NPC
from t5code.T5ShipClass import T5ShipClass
from t5code.T5Tables import POSITIONS
from t5code.T5Exceptions import (
    InsufficientFundsError,
    CapacityExceededError,
    InvalidPassageClassError,
    DuplicateItemError,
    WorldNotFoundError,
    InvalidLotTypeError,
    InvalidThresholdError,
)

if TYPE_CHECKING:
    from t5code.T5Mail import T5Mail


class CrewPosition:
    """Represents a crew position on a starship with optional NPC assignment.

    Provides methods to check if a position is filled and to get/set the
    assigned NPC.

    Attributes:
        position_code: Single-letter code from POSITIONS table
        position_name: Full position name from POSITIONS table
        npc: The T5NPC assigned to this position, or None if unfilled
    """

    def __init__(self, position_code: str) -> None:
        """Initialize crew position with code from POSITIONS table.

        Args:
            position_code: Single-letter or digit code (e.g., 'A', '0')
        """
        self.position_code = position_code
        self.position_name = POSITIONS.get(position_code,
                                           f"Unknown-{position_code}")
        self.npc: Optional[T5NPC] = None

    def is_filled(self) -> bool:
        """Check if position has an assigned crew member.

        Returns:
            True if position has an NPC assigned, False otherwise
        """
        return self.npc is not None

    def assign(self, npc: T5NPC) -> None:
        """Assign an NPC to this position.

        Args:
            npc: The T5NPC to assign to this position
        """
        self.npc = npc

    def clear(self) -> None:
        """Remove the assigned NPC from this position."""
        self.npc = None

    def __repr__(self) -> str:
        """String representation of crew position."""
        status = (f"filled by {self.npc.character_name}"
                  if self.is_filled() else "vacant")
        return (f"CrewPosition({self.position_code}: "
                f"{self.position_name}, {status})")


class _BestCrewSkillDict:
    """Dictionary-like interface for finding best crew skill levels.

    Provides a convenient way to query the maximum skill level across all
    crew members for any given skill. Used via T5Starship.best_crew_skill.

    Example:
        # Returns highest pilot skill on crew
        >>> ship.best_crew_skill["pilot"]
        3
    """

    def __init__(self, crew_dict: Dict[str, T5NPC]) -> None:
        """Initialize with crew dictionary.

        Args:
            crew_dict: Dictionary mapping crew positions to T5NPC instances
        """
        self.crew: Dict[str, T5NPC] = crew_dict

    def __getitem__(self, skill_name: str) -> int:
        """Get highest skill level for this skill across all crew.

        Args:
            skill_name: Name of skill (case insensitive)

        Returns:
            Highest skill level among crew (0 if no crew has the skill)
        """
        skill_name = skill_name.lower()
        return max(
            (member.get_skill(skill_name) for member in self.crew.values()),
            default=0
        )


class T5Starship:
    """Starship with cargo, passengers, crew, and financial operations.

    Implements T5 starship operations including:
    - Passenger and crew management with capacity limits
    - Cargo and freight loading with hold size constraints
    - Mail transport with locker capacity
    - Financial tracking (credits in/out)
    - Navigation (location and destination)

    Capacity is managed realistically:
    - High/mid passengers share staterooms
    - Low passengers use separate low berths
    - Cargo and freight share hold space (measured in tons)
    - Mail uses dedicated locker slots

    Attributes:
        ship_name: Ship's name
        location: Current world name
        hold_size: Cargo capacity in tons
        staterooms: Number of staterooms (for high/mid passengers)
        low_berths: Number of low berth slots
        passengers: Dict of passenger sets by class ('high', 'mid', 'low')
        mail: Dict of mail bundles by serial
        crew: Dict of crew NPCs by position
        cargo: Dict of cargo/freight lots by type
        cargo_size: Current cargo tonnage
        mail_locker_size: Maximum mail bundles

    Properties:
        destination: Destination world name
        mail_bundles: Current mail containers
        cargo_manifest: Current cargo/freight lots
        balance: Current credits
        best_crew_skill: Query interface for max crew skill levels

    Example:
        >>> ship = T5Starship("Beowulf", "Rhylanor", ship_class)
        >>> ship.credit(100000)  # Starting funds
        >>> ship.hire_crew("pilot", pilot_npc)
        >>> ship.set_course_for("Jae Tellona")
    """

    def _get_stateroom_passenger_count(self) -> int:
        """Get current number of passengers using staterooms.

        Returns:
            Total count of high and mid passengers
        """
        return len(self.passengers["high"]) + len(self.passengers["mid"])

    def __init__(self,
                 ship_name: str,
                 ship_location: str,
                 ship_class: T5ShipClass) -> None:
        """Create a new starship.

        Args:
            ship_name: Name of the ship
            ship_location: Starting world/location
            ship_class: T5ShipClass instance defining ship specifications
        """
        # Core identity
        self.ship_name: str = ship_name
        self.location: str = ship_location
        self.ship_class: str = ship_class.class_name
        self.hold_size: int = ship_class.cargo_capacity
        self.jump_rating: int = ship_class.jump_rating

        # Passenger capacity (high and mid use staterooms, low uses low berths)
        self.staterooms: int = ship_class.staterooms
        self.low_berths: int = ship_class.low_berths

        # Passenger system
        self.high_passengers: Set[T5NPC] = set()
        self.passengers: Dict[str, Set[T5NPC]] = {
            "high": set(),
            "mid": set(),
            "low": set(),
            "all": set(),  # useful for global queries or summary stats
        }

        # Mail, crew, and cargo tracking
        self.mail: Dict[str, "T5Mail"] = {}  # mail_id → T5Mail object
        self.crew: Dict[str, T5NPC] = {}  # role → T5NPC or crew record

        # Crew positions from ship class design
        # (supports multiple of same type)
        # Dict[position_name, List[CrewPosition]]
        self.crew_position: Dict[str, List[CrewPosition]] = {}
        for position_code in ship_class.crew_positions:
            position_name = POSITIONS.get(position_code,
                                          f"Unknown-{position_code}")
            if position_name not in self.crew_position:
                self.crew_position[position_name] = []
            (self.crew_position[position_name].
             append(CrewPosition(position_code)))

        self.cargo: Dict[str, List[T5Lot]] = {
            "freight": [],  # freight lots
            "cargo": [],  # miscellaneous or special cargo
        }
        self.cargo_size: int = 0  # total tons of cargo on board
        self.mail_locker_size: int = 1  # max number of mail containers

        # Navigation
        # Destination world assigned when a flight plan is set
        self._destination: str = "Unassigned"
        # Financials # in credits (millions, thousands — your scale)
        self._balance: float = 0.0

    def set_course_for(self, destination: str) -> None:
        """Set the ship's destination world.

        Updates the destination property to the specified world name.

        Args:
            destination: Name of the destination world
        """
        self._destination = destination

    @property
    def destination(self) -> str:
        """Current destination world name.

        Returns:
            Name of the destination world, or 'Unassigned' if no course is set
        """
        return self._destination

    def onload_passenger(self, npc: T5NPC, passage_class: str) -> None:
        """Load a passenger onto the ship.

        Args:
            npc: The NPC passenger to load
            passage_class: Passage class ('high', 'mid', or 'low')

        Raises:
            TypeError: If npc is not a T5NPC instance
            InvalidPassageClassError: If passage_class is invalid
            DuplicateItemError: If passenger is already on board
            CapacityExceededError: If no capacity available
        """
        if not isinstance(npc, T5NPC):
            raise TypeError("Invalid passenger type.")

        ALLOWED_PASSAGE_CLASSES = ("high", "mid", "low")
        if passage_class not in ALLOWED_PASSAGE_CLASSES:
            raise InvalidPassageClassError(
                passage_class,
                ALLOWED_PASSAGE_CLASSES)

        if npc in self.passengers["all"]:
            raise DuplicateItemError(npc.character_name, "passenger")

        # Check capacity - high and mid use staterooms, low uses low berths
        if passage_class in ["high", "mid"]:
            stateroom_passengers = (len(self.passengers["high"])
                                    + len(self.passengers["mid"]))
            if stateroom_passengers >= self.staterooms:
                raise CapacityExceededError(
                    required=1,
                    available=self.staterooms - stateroom_passengers,
                    capacity_type="staterooms"
                )
        elif passage_class == "low":
            if len(self.passengers["low"]) >= self.low_berths:
                raise CapacityExceededError(
                    required=1,
                    available=self.low_berths - len(self.passengers["low"]),
                    capacity_type="low berths"
                )

        self.passengers["all"].add(npc)
        self.passengers[passage_class].add(npc)
        npc.location = self.ship_name

    def offload_passengers(self, passage_class: str) -> Set[T5NPC]:
        """Offload all passengers of a specific class.

        Args:
            passage_class: Passage class to offload ('high', 'mid', or 'low')

        Returns:
            Set of offloaded NPC passengers

        Raises:
            InvalidPassageClassError: If passage_class is invalid
        """
        offloaded_passengers: Set[T5NPC] = set()
        allowed_passage_classes = ("high", "mid", "low")

        if passage_class not in allowed_passage_classes:
            raise InvalidPassageClassError(
                passage_class,
                allowed_passage_classes)

        for npc in set(self.passengers[passage_class]):
            if passage_class == "low":
                self.awaken_low_passenger(
                    npc,
                    self.crew.get("medic"),
                )
            npc.location = self.location
            self.passengers[passage_class].remove(npc)
            self.passengers["all"].remove(npc)
            offloaded_passengers.add(npc)

        return offloaded_passengers

    def awaken_low_passenger(self,
                             npc: T5NPC,
                             medic,
                             roll_override_in: int = None):
        """Awaken a low passage passenger from cold sleep.

        Low passage has a risk of death (5+ on 2d6 to survive). A medic's
        Medicine skill provides DM bonus to the survival roll.

        Args:
            npc: The passenger to awaken
            medic: Medic NPC (or None if no medic available)
            roll_override_in: Override for survival roll (testing only)

        Note:
            Calls npc.kill() if survival roll fails
        """
        medic_skills = medic.skills if medic else None
        if check_success(roll_override=roll_override_in,
                         skills_override=medic_skills):
            return True
        else:
            npc.kill()
            return False

    def onload_mail(self, mail_item: "T5Mail") -> None:
        """Load a mail container onto the ship.

        Args:
            mail_item: Mail container to load

        Raises:
            ValueError: If mail locker is full
        """
        if len(self.mail.keys()) >= self.mail_locker_size:
            raise ValueError("Starship mail locker size exceeded.")
        self.mail[mail_item.serial] = mail_item

    def offload_mail(self) -> None:
        """Offload all mail from the ship.

        Clears the mail dictionary, removing all mail containers.

        Raises:
            ValueError: If ship has no mail to offload
        """
        if len(self.mail.keys()) == 0:
            raise ValueError("Starship has no mail to offload.")
        self.mail = {}

    @property
    def mail_bundles(self) -> Dict[str, "T5Mail"]:
        """Dictionary of mail bundles currently on board.

        Returns:
            Dict mapping mail serial numbers to T5Mail objects
        """
        return self.mail

    def hire_crew(self, position: str, npc: T5NPC) -> None:
        """Hire a crew member for a specific position.

        Args:
            position: Crew position identifier
            npc: The NPC to hire

        Raises:
            TypeError: If npc is not a T5NPC instance
        """
        if not isinstance(npc, T5NPC):
            raise TypeError("Invalid NPC.")
        self.crew[position] = npc

    @property
    def best_crew_skill(self):
        """Helper for finding best crew skill values.

        Returns:
            _BestCrewSkillDict that looks up highest skill level across crew
        """
        return _BestCrewSkillDict(self.crew)

    ALLOWED_LOT_TYPES = ("cargo", "freight")

    def can_onload_lot(self, in_lot: T5Lot, lot_type: str) -> bool:
        """Check if a lot can be loaded onto the ship.

        Args:
            in_lot: The lot to check
            lot_type: Type of lot ('cargo' or 'freight')

        Returns:
            True if lot can be loaded

        Raises:
            TypeError: If in_lot is not a T5Lot instance
            InvalidLotTypeError: If lot_type is invalid
            CapacityExceededError: If lot won't fit
            DuplicateItemError: If lot is already loaded
        """
        if not isinstance(in_lot, T5Lot):
            raise TypeError("Invalid lot type.")

        if lot_type not in self.ALLOWED_LOT_TYPES:
            raise InvalidLotTypeError(lot_type, self.ALLOWED_LOT_TYPES)

        if in_lot.mass + self.cargo_size > self.hold_size:
            raise CapacityExceededError(
                required=in_lot.mass,
                available=self.hold_size - self.cargo_size,
                capacity_type="cargo hold"
            )

        if in_lot in self.cargo["freight"] or in_lot in self.cargo["cargo"]:
            raise DuplicateItemError(in_lot.serial, "lot")

        return True  # explicitly returns True if all checks pass

    def onload_lot(self, in_lot, lot_type):
        """Load a cargo lot onto the ship.

        Args:
            in_lot: The lot to load
            lot_type: Type of lot ('cargo' or 'freight')

        Raises:
            Same as can_onload_lot()

        Note:
            Calls can_onload_lot() which performs all validation
        """
        if self.can_onload_lot(in_lot, lot_type):
            self.cargo[lot_type].append(in_lot)
            self.cargo_size += in_lot.mass

    def offload_lot(self, in_serial: str, lot_type: str) -> "T5Lot":
        """Offload a specific cargo lot by serial number.

        Args:
            in_serial: UUID serial number of the lot
            lot_type: Type of lot ('cargo' or 'freight')

        Returns:
            The offloaded lot

        Raises:
            ValueError: If serial number is invalid UUID
            InvalidLotTypeError: If lot_type is invalid
            ValueError: If lot not found
        """
        try:
            uuid.UUID(in_serial)
        except ValueError:
            raise ValueError("Invalid lot serial number.")
        if not ((lot_type == "cargo") or (lot_type == "freight")):
            raise InvalidLotTypeError(lot_type, self.ALLOWED_LOT_TYPES)
        result = next((lot for lot in self.cargo[
            lot_type] if lot.serial == in_serial), None)

        if result is None:
            raise ValueError("Lot not found as specified type.")
        else:
            self.cargo[lot_type].remove(result)
            self.cargo_size -= result.mass
            return result

    @property
    def cargo_manifest(self) -> Dict[str, List[T5Lot]]:
        """Dictionary of cargo and freight lots currently on board.

        Returns:
            Dict with 'cargo' and 'freight'
            keys mapping to lists of T5Lot objects
        """
        return self.cargo

    @property
    def balance(self):
        """Ship's current credit balance.

        Returns:
            Current balance in credits (float)
        """
        return self._balance

    def credit(self, amount):
        """Add credits to the ship's balance.

        Args:
            amount: Credits to add (int or float)

        Raises:
            TypeError: If amount is not a number
            ValueError: If amount is negative
        """
        if not isinstance(amount, (int, float)):
            raise TypeError("Amount must be a number")
        if amount < 0:
            raise ValueError("Cannot credit a negative amount")
        self._balance += amount

    def debit(self, amount):
        """Subtract money from the ship's balance.

        Args:
            amount: Amount of credits to debit

        Raises:
            TypeError: If amount is not a number
            ValueError: If amount is negative
            InsufficientFundsError: If insufficient funds available
        """
        if not isinstance(amount, (int, float)):
            raise TypeError("Amount must be a number")
        if amount < 0:
            raise ValueError("Cannot debit a negative amount")
        if amount > self._balance:
            raise InsufficientFundsError(
                required=amount,
                available=self._balance)
        self._balance -= amount

    def load_passengers(self, world) -> Dict[str, int]:
        """Search for and load passengers based on crew skills and capacity.

        Rolls for passenger availability using:
        - High passengers: Steward skill modifier
        - Mid passengers: Admin skill modifier
        - Low passengers: Streetwise skill modifier

        Loads passengers up to ship capacity and available numbers.
        Ship is credited with passenger fares.

        Args:
            world: T5World instance for the current location

        Returns:
            Dictionary with counts: {"high": n, "mid": n, "low": n}
        """
        from t5code.T5Tables import PASSENGER_FARES

        # Calculate available capacity
        current_stateroom_passengers = (len(self.passengers["high"]) +
                                        len(self.passengers["mid"]))
        available_staterooms = self.staterooms - current_stateroom_passengers
        available_low_berths = self.low_berths - len(self.passengers["low"])

        # Roll for passenger availability using crew skills
        high_available = world.high_passenger_availability(
            self.best_crew_skill["Steward"]
        )
        mid_available = world.mid_passenger_availability(
            self.best_crew_skill["Admin"]
        )
        low_available = world.low_passenger_availability(
            self.best_crew_skill["Streetwise"]
        )

        loaded = {"high": 0, "mid": 0, "low": 0}

        # Load high passengers (limited by availability AND ship capacity)
        high_to_load = min(high_available, available_staterooms)
        for i in range(high_to_load):
            try:
                npc = T5NPC(f"High Passenger {i+1}")
                self.onload_passenger(npc, "high")
                self.credit(PASSENGER_FARES["high"])
                loaded["high"] += 1
            except ValueError:
                break

        # Load mid passengers (limited by
        # availability AND remaining staterooms)
        current_stateroom_passengers = (len(self.passengers["high"]) +
                                        len(self.passengers["mid"]))
        remaining_staterooms = self.staterooms - current_stateroom_passengers
        mid_to_load = min(mid_available, remaining_staterooms)
        for i in range(mid_to_load):
            try:
                npc = T5NPC(f"Mid Passenger {i+1}")
                self.onload_passenger(npc, "mid")
                self.credit(PASSENGER_FARES["mid"])
                loaded["mid"] += 1
            except ValueError:
                break

        # Load low passengers (limited by availability AND low berth capacity)
        low_to_load = min(low_available, available_low_berths)
        for i in range(low_to_load):
            try:
                npc = T5NPC(f"Low Passenger {i+1}")
                self.onload_passenger(npc, "low")
                self.credit(PASSENGER_FARES["low"])
                loaded["low"] += 1
            except ValueError:
                break

        return loaded

    def sell_cargo_lot(self, lot: "T5Lot", game_state,
                       use_trader_skill: bool = True) -> dict:
        """Sell a cargo lot at the current
        world using broker and trader skills.

        Args:
            lot: The cargo lot to sell
            game_state: GameState object with world_data
            use_trader_skill: Whether to use trader skill for prediction

        Returns:
            Dictionary with keys:
                'final_amount': Final credits received after broker fee
                'gross_amount': Amount before broker fee
                'broker_fee': Broker fee amount
                'profit': Net profit/loss
                'purchase_cost': Original purchase cost
                'modifier': Final price multiplier
                'flux_info': Dict with flux details
                if trader skill used, else None

        Raises:
            ValueError: If lot is not in cargo hold
            WorldNotFoundError: If current location
            world not found in game data
        """
        from t5code import find_best_broker
        from t5code.T5Tables import ACTUAL_VALUE

        # Verify lot is in cargo
        if lot not in self.cargo_manifest["cargo"]:
            raise ValueError(f"Lot {lot.serial} is not in cargo hold")

        # Get world
        world = game_state.world_data.get(self.location)
        if not world:
            raise WorldNotFoundError(self.location)

        # Get broker info
        broker = find_best_broker(world.get_starport())
        broker_mod = broker["mod"]
        broker_rate = broker["rate"]

        # Calculate sale value at destination
        value = lot.determine_sale_value_on(self.location, game_state)

        # Get trader skill if available
        trader = self.crew.get("crew1")
        has_trader = (use_trader_skill and trader and
                      trader.get_skill("trader") > 0)
        trader_skill = trader.get_skill("trader") if has_trader else 0

        flux_info = None

        # Get price multiplier
        if has_trader:
            # Use trader skill to predict market
            min_mult, max_mult, flux = lot.predict_actual_value_range(
                broker_mod)

            # Complete the roll
            final_flux = flux.roll_second()
            clamped = max(-5, min(8, final_flux + broker_mod))
            modifier = ACTUAL_VALUE[clamped]

            flux_info = {
                'trader_skill': trader_skill,
                'first_die': flux.first_die,
                'second_die': flux.second_die,
                'min_multiplier': min_mult,
                'max_multiplier': max_mult,
                'final_flux': final_flux,
                'final_multiplier': modifier
            }
        else:
            # No trader skill, roll normally
            modifier = lot.consult_actual_value_table(broker_mod)

        # Calculate amounts
        gross_amount = value * modifier
        broker_fee = gross_amount * broker_rate
        final_amount = gross_amount - broker_fee
        purchase_cost = lot.origin_value * lot.mass
        profit = final_amount - purchase_cost

        # Execute transaction
        self.credit(final_amount)
        self.offload_lot(lot.serial, "cargo")

        return {
            'final_amount': final_amount,
            'gross_amount': gross_amount,
            'broker_fee': broker_fee,
            'profit': profit,
            'purchase_cost': purchase_cost,
            'modifier': modifier,
            'flux_info': flux_info
        }

    def buy_cargo_lot(self, lot: "T5Lot") -> None:
        """Purchase and load a speculative cargo lot.

        Debits the ship's balance and loads the lot into cargo hold.
        If loading fails (e.g., capacity exceeded), the debit is rolled back.

        Args:
            lot: The cargo lot to purchase

        Raises:
            InsufficientFundsError: If insufficient funds for purchase
            CapacityExceededError: If insufficient hold space
            DuplicateItemError: If lot is already loaded
        """
        cost = lot.origin_value * lot.mass
        self.debit(cost)
        try:
            self.onload_lot(lot, "cargo")
        except (CapacityExceededError, DuplicateItemError):
            # Rollback debit if loading fails
            self.credit(cost)
            raise

    def load_freight_lot(self, lot: "T5Lot") -> float:
        """Load a freight lot and receive payment.

        Args:
            lot: The freight lot to load

        Returns:
            The freight payment amount

        Raises:
            ValueError: If hold space insufficient
        """
        from t5code.T5Tables import FREIGHT_RATE_PER_TON

        self.onload_lot(lot, "freight")
        payment = FREIGHT_RATE_PER_TON * lot.mass
        self.credit(payment)
        return payment

    def load_mail(self, game_state, destination: str) -> "T5Mail":
        """Create and load a mail bundle for the destination.

        Args:
            game_state: GameState object with world_data
            destination: Destination world name

        Returns:
            The loaded mail bundle

        Raises:
            ValueError: If mail capacity exceeded
        """
        from t5code import T5Mail

        mail_lot = T5Mail(self.location, destination, game_state)
        self.onload_mail(mail_lot)
        return mail_lot

    def is_hold_mostly_full(self, threshold: float = 0.8) -> bool:
        """Check if cargo hold is at or above a threshold percentage.

        Args:
            threshold: Percentage of hold capacity (0.0-1.0).
            Default is 0.8 (80%).

        Returns:
            True if cargo_size >= threshold * hold_size, False otherwise

        Raises:
            InvalidThresholdError: If threshold is not between 0 and 1
        """
        if threshold < 0 or threshold > 1:
            raise InvalidThresholdError(threshold, 0.0, 1.0)
        return self.cargo_size >= threshold * self.hold_size

    def execute_jump(self, destination: str) -> None:
        """Execute a jump to destination with proper status transitions.

        This method encapsulates the complete jump sequence:
        1. Set course for destination
        2. Maneuver to jump point (status: maneuvering)
        3. Jump to destination system (status: traveling)
        4. Arrive and maneuver to starport (status: maneuvering)
        5. Dock at starport (status: docked)

        Args:
            destination: Name of destination world
        """
        self.set_course_for(destination)
        self.status = "maneuvering"
        # Ship is now maneuvering to jump point
        self.status = "traveling"
        # Ship is now jumping
        self.location = self.destination
        self.status = "maneuvering"
        # Ship is now maneuvering to starport
        self.status = "docked"
        # Ship has docked at starport

    def get_worlds_in_jump_range(self, game_state) -> List[str]:
        """Get all worlds reachable with this ship's jump drive.

        Calculates hex distance from current location to all other worlds
        and returns those within the ship's jump rating.

        Args:
            game_state: GameState instance with world_data

        Returns:
            List of world names reachable by this ship's jump drive

        Raises:
            WorldNotFoundError: If current location not found in world_data
        """
        # Get current world data
        current_world = game_state.world_data.get(self.location)
        if not current_world:
            raise WorldNotFoundError(self.location)

        current_coords = current_world.world_data["Coordinates"]
        reachable_worlds = []

        for world_name, world_obj in game_state.world_data.items():
            # Skip current world
            if world_name == self.location:
                continue

            # Skip Amber/Red zones
            zone = world_obj.world_data.get("Zone", "G")
            if zone in ["A", "R"]:
                continue

            # Calculate hex distance using Traveller formula:
            # max of absolute differences in x, y, and diagonal
            target_coords = world_obj.world_data["Coordinates"]
            x1, y1 = current_coords
            x2, y2 = target_coords
            distance = max(
                abs(x1 - x2),
                abs(y1 - y2),
                abs((x1 - y1) - (x2 - y2))
            )

            if distance <= self.jump_rating:
                reachable_worlds.append(world_name)

        return reachable_worlds

    def find_profitable_destinations(self,
                                     game_state) -> List[Tuple[str, int]]:
        """Find destinations where cargo from
        current location can sell at profit.

        Creates a sample cargo lot from the current world and evaluates
        potential profit at each reachable destination. Only returns
        destinations where profit is positive.

        Args:
            game_state: GameState instance with world_data

        Returns:
            List of (world_name, estimated_profit) tuples,
            sorted by profit descending

        Raises:
            WorldNotFoundError: If current location not found in world_data

        Example:
            >>> profitable = ship.find_profitable_destinations(game_state)
            >>> if profitable:
            ...     best_dest, profit = profitable[0]
            ...     print(f"{best_dest}: +Cr{profit}/ton")
        """
        from t5code.T5Lot import T5Lot

        # Get worlds in jump range
        reachable_worlds = self.get_worlds_in_jump_range(game_state)
        if not reachable_worlds:
            return []

        # Create sample lot from current world
        sample_lot = T5Lot(self.location, game_state)
        sample_lot.mass = 1  # 1 ton for per-ton profit calculation
        purchase_price = sample_lot.origin_value

        profitable_destinations = []
        for world_name in reachable_worlds:
            sale_value = sample_lot.determine_sale_value_on(world_name,
                                                            game_state)
            profit_per_ton = sale_value - purchase_price

            if profit_per_ton > 0:
                profitable_destinations.append((world_name, profit_per_ton))

        # Sort by profit descending
        profitable_destinations.sort(key=lambda x: x[1], reverse=True)
        return profitable_destinations

    def offload_all_freight(self) -> List[T5Lot]:
        """Offload all freight lots from the ship.

        Returns:
            List of offloaded freight lots
        """
        freight_lots = list(self.cargo_manifest.get("freight", []))
        for lot in freight_lots:
            self.offload_lot(lot.serial, "freight")
        return freight_lots
