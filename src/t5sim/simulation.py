"""Main SimPy simulation orchestrator.

Manages the discrete-event simulation of multiple merchant starships
using t5code for game mechanics. Provides the Simulation class which
handles SimPy environment setup, agent creation, statistics tracking,
and results reporting.

The orchestrator separates concerns:
    - t5code handles all game mechanics (trading, cargo, passengers)
    - t5sim handles discrete-event timing and multi-agent coordination
    - StarshipAgent implements individual ship AI behavior

This architecture enables large-scale simulations (100+ ships, 1000+
days) to complete in seconds while maintaining game-accurate mechanics.
"""

from typing import List, Dict, Any
import simpy
from t5code import T5NPC, T5ShipClass, T5Company
from t5code.T5NPC import generate_captain_risk_profile
from t5code.GameState import GameState
from t5code.T5Starship import T5Starship
from t5sim.starship_agent import StarshipAgent
from t5sim.starship_states import StarshipState


class Simulation:
    """Main simulation controller for merchant starship operations.

    Orchestrates SimPy discrete-event simulation of multiple merchant
    starships executing independent trading operations. Manages the
    SimPy environment, creates agents, tracks statistics, and
    generates results.

    Attributes:
        env: SimPy environment for discrete-event simulation
        game_state: GameState with world and ship class data
        agents: List of active StarshipAgent instances
        statistics: Collected simulation data (cargo_sales, etc)
        num_ships: Number of ships in simulation
        duration_days: Total simulation duration
        starting_capital: Initial credits per ship
        verbose: Whether to print detailed status updates
        starting_year: Traveller calendar year (default: 1104)
        starting_day: Day of year 1-365 (default: 360)
    """

    def __init__(
        self,
        game_state: GameState,
        num_ships: int = 10,
        duration_days: float = 365.0,
        starting_capital: float = 1_000_000.0,
        verbose: bool = False,
        starting_year: int = 1104,
        starting_day: int = 360,
    ):
        """Initialize the simulation with environment and settings.

        Creates SimPy environment and initializes simulation
        parameters. Does not create ships or agents yet; call
        setup() followed by run() to execute the simulation.

        Args:
            game_state: Initialized GameState with world and ship
                        data loaded
            num_ships: Number of starships to simulate (default: 10)
            duration_days: Simulation duration in days, can be
                           fractional (default: 365.0)
            starting_capital: Starting capital per ship in credits
                              (default: 1,000,000)
            verbose: Print detailed status updates during simulation
                     (default: False)
            starting_year: Starting year in Traveller calendar
                           (default: 1104)
            starting_day: Starting day of year, 1-365
                          (default: 360)

        Note:
            Verbose mode generates substantial output for large
            simulations; recommended only for debugging or small
            runs (< 10 ships, < 100 days).
        """
        self.env = simpy.Environment()
        self.game_state = game_state
        self.num_ships = num_ships
        self.duration_days = duration_days
        self.starting_capital = starting_capital
        self.verbose = verbose
        self.starting_year = starting_year
        self.starting_day = starting_day

        self.agents: List[StarshipAgent] = []
        self.statistics: Dict[str, List[Any]] = {
            "cargo_sales": [],  # List of sale transactions
            "ship_balances": [],  # Periodic balance snapshots
            "trade_routes": [],  # Route usage tracking
        }

    def format_traveller_date(self, sim_time: float) -> str:
        """Convert simulation time to Traveller date format (DDD.FF-YYYY).

        Args:
            sim_time: Simulation time in days (can be fractional)

        Returns:
            Formatted date string like '001.00-1105' or '365.50-1104'

        Example:
            >>> sim.format_traveller_date(0.0)
            # '360.00-1104' (if starting_day=360)
            >>> sim.format_traveller_date(1.5)
            # '361.50-1104'
            >>> sim.format_traveller_date(6.0)
            # '001.00-1105' (if starting_day=360)
        """
        # Calculate absolute day from start (preserve fractional part)
        total_days = self.starting_day + sim_time

        # Calculate year offset (every 365 days = 1 year)
        years_elapsed = int((total_days - 1) // 365)
        day_of_year = ((total_days - 1) % 365) + 1

        current_year = self.starting_year + years_elapsed

        # Split into integer and fractional parts
        day_int = int(day_of_year)
        day_frac = day_of_year - day_int

        return f"{day_int:03d}.{day_frac * 100:02.0f}-{current_year}"

    def setup(self):
        """Create starships and agents for simulation.

        Generates num_ships merchant starships with random starting
        worlds and ship classes. Each ship receives starting capital
        and basic crew (trader, steward, admin, liaison, medic).
        Creates StarshipAgent wrapper for each ship and adds to
        agents list.

        Side Effects:
            - Populates self.agents with StarshipAgent instances
            - Each agent automatically starts its SimPy process
            - Ships only placed at worlds with reachable destinations
            - Each ship picks initial destination in jump range

        Note:
            Called automatically by run() if needed, but can be
            called separately for inspection before execution.
        """
        import random
        from t5code import T5ShipClass

        worlds = list(self.game_state.world_data.keys())
        ship_classes_data = list(self.game_state.ship_classes.values())

        for i in range(self.num_ships):
            # Pick random ship class first
            ship_class_dict = random.choice(ship_classes_data)
            class_name = ship_class_dict["class_name"]
            ship_class = T5ShipClass(class_name, ship_class_dict)

            # Find a starting world with valid destinations
            # Try up to 100 times to find ideal location
            starting_world = None
            reachable_worlds = []
            attempts = 100
            for _ in range(attempts):
                candidate_world = random.choice(worlds)
                # Create temporary ship to check jump range
                temp_ship = T5Starship(
                    "temp", candidate_world, ship_class
                )
                reachable_worlds = temp_ship.get_worlds_in_jump_range(
                    self.game_state
                )
                if reachable_worlds:
                    starting_world = candidate_world
                    break

            # Fallback: if no valid location found, use any world
            # (may happen with small test maps or isolated worlds)
            if not starting_world:
                starting_world = random.choice(worlds)
                # Ship will pick destination during first jump via
                # _choose_next_destination()
                reachable_worlds = []

            # Create company for this ship
            company = T5Company(
                f"Trader_{i + 1:03d} Inc",
                starting_capital=self.starting_capital
            )

            # Create actual ship with company ownership
            ship = T5Starship(
                f"Trader_{i + 1:03d}", starting_world, ship_class,
                owner=company
            )

            # Add basic crew (pass ship_class since
            # ship stores class_name string)
            self._add_basic_crew(ship, ship_class)

            # Pick initial destination using StarshipAgent's logic
            if reachable_worlds:
                destination = StarshipAgent.pick_destination(
                    ship, self.game_state
                )
                ship.set_course_for(destination)
            else:
                # No destinations available (isolated world or small map)
                # Set to current location to prevent crashes
                ship.set_course_for(starting_world)

            # Create agent
            agent = StarshipAgent(
                self.env, ship, self,
                starting_state=StarshipState.DOCKED
            )
            self.agents.append(agent)

    def _get_skill_for_position(
        self,
        position_name: str,
        position_index: int,
        ship_class: T5ShipClass
    ) -> tuple[str, int] | None:
        """Determine skill name and level for a crew position.

        Args:
            position_name: Name of position (e.g., "Pilot", "Engineer")
            position_index: Index in position list (0 = first/chief)
            ship_class: T5ShipClass for ship-attribute-based skills

        Returns:
            Tuple of (skill_name, skill_level) or None if no skill
        """
        # Check if this is a Captain serving as Pilot
        # (no separate Pilot position)
        has_pilot = "A" in ship_class.crew_positions
        if position_name == "Captain" and not has_pilot:
            return ("Pilot", ship_class.maneuver_rating)
        elif position_name == "Pilot":
            return ("Pilot", ship_class.maneuver_rating)
        elif position_name == "Astrogator":
            return ("Astrogator", ship_class.jump_rating)
        elif position_name == "Engineer":
            # Chief Engineer (first one) gets +1 skill level
            level = (ship_class.powerplant_rating + 1
                     if position_index == 0
                     else ship_class.powerplant_rating)
            return ("Engineer", level)
        elif position_name == "Steward":
            return ("Steward", 3)
        elif position_name == "Gunner":
            return ("Gunner", 1)
        elif position_name == "Counsellor":
            return ("Counsellor", 2)
        elif position_name == "Medic":
            return ("Medic", 2)
        return None

    def _add_basic_crew(self, ship: T5Starship, ship_class: T5ShipClass):
        """Add crew NPCs to fill all positions defined by the ship class.

        Creates NPCs for each position slot in ship.crew_position.
        Assigns skills based on position type and ship attributes:
        - Pilot: pilot-n (n = maneuver_rating)
        - Astrogator: navigation-n (n = jump_rating)
        - Engineer: engineer-n (n = powerplant_rating)
          * Chief Engineer (first): engineer-(powerplant_rating + 1)
        - Steward: steward-3
        - Gunner: gunner-1
        - Counsellor: counsellor-2
        - Medic: medic-2
        - All other positions: no skills

        Captain gets special treatment with random risk profile.
        On ships without explicit Captain position, Pilot serves as Captain.

        Args:
            ship: T5Starship to crew
            ship_class: T5ShipClass object with ship specifications
        """
        # Check if ship has explicit captain position
        has_captain = "Captain" in ship.crew_position

        # Fill each position slot with an NPC
        for position_name, position_list in ship.crew_position.items():
            for i, crew_position in enumerate(position_list):
                # Generate unique name for multiple positions
                npc_name = (f"{position_name} {i+1}"
                            if len(position_list) > 1
                            else position_name)

                # Create NPC and assign skill if applicable
                npc = T5NPC(npc_name)
                skill_info = self._get_skill_for_position(
                    position_name, i, ship_class
                )
                if skill_info:
                    npc.set_skill(skill_info[0], skill_info[1])

                # Add risk profile to Captain or Pilot (if no Captain)
                if (position_name == "Captain" or (position_name == "Pilot"
                                                   and not has_captain
                                                   and i == 0)):
                    npc.cargo_departure_threshold = (
                        generate_captain_risk_profile()
                    )

                # Assign NPC to position slot
                crew_position.assign(npc)

    def run(self) -> Dict[str, Any]:
        """Run the simulation to completion.

        Executes the full simulation: calls setup() to create ships
        and agents, runs SimPy environment until duration_days,
        then generates and returns results dictionary.

        Returns:
            Dictionary of simulation results and statistics:
            - duration_days: Simulation length
            - num_ships: Number of ships simulated
            - total_voyages: Sum of all completed voyages
            - cargo_sales: Count of cargo transactions
            - total_profit: Sum of profit/loss vs starting capital
            - ships: List of per-ship details (name, balance,
                     voyages, location)

        Side Effects:
            - Prints progress messages during execution
            - Populates self.statistics with transaction data

        Example:
            >>> sim = Simulation(game_state, num_ships=10)
            >>> results = sim.run()
            >>> print(f"Profit: Cr{results['total_profit']:,.0f}")
        """
        print(f"Setting up simulation with {self.num_ships} ships...")
        print(f"Running simulation for {self.duration_days} days...")
        self.setup()

        self.env.run(until=self.duration_days)

        print("Simulation complete. Generating results...")
        return self._generate_results()

    def _generate_results(self) -> Dict[str, Any]:
        """Generate summary results from completed simulation.

        Aggregates data from all agents and statistics to produce
        comprehensive results dictionary. Calculates total profit
        as change from starting_capital across all ships.

        Returns:
            Dictionary with simulation statistics:
            - duration_days: Simulation length
            - num_ships: Number of ships
            - total_voyages: Sum of completed voyages
            - cargo_sales: Count of cargo transactions
            - total_profit: Total Cr profit/loss vs starting
            - ships: List of per-ship data dictionaries

        Note:
            Called internally by run(); not typically called
            directly by users.
        """
        # Calculate total profit as change from starting capital
        total_profit = sum(
            agent.ship.balance - self.starting_capital
            for agent in self.agents
        )

        results = {
            "duration_days": self.duration_days,
            "num_ships": self.num_ships,
            "total_voyages": sum(agent.voyage_count for agent in self.agents),
            "cargo_sales": len(self.statistics["cargo_sales"]),
            "total_profit": total_profit,
            "ships": [
                {
                    "name": agent.ship.ship_name,
                    "balance": agent.ship.balance,
                    "voyages": agent.voyage_count,
                    "location": agent.ship.location,
                }
                for agent in self.agents
            ],
        }
        return results

    def record_cargo_sale(self,
                          ship_name: str,
                          location: str,
                          profit: float):
        """Record a cargo sale transaction for statistics.

        Logs cargo sale details to statistics['cargo_sales'] list
        for post-simulation analysis. Called by agents during
        SELLING_CARGO state.

        Args:
            ship_name: Name of ship making sale
            location: World where sale occurred
            profit: Profit or loss from sale in credits (can be
                    negative)

        Side Effects:
            Appends transaction dict to self.statistics['cargo_sales']
            with fields: time, ship, location, profit

        Note:
            Could be extended to track freight income, passenger
            fares, mail payments, etc. for comprehensive financial
            analysis.
        """
        self.statistics["cargo_sales"].append(
            {
                "time": self.env.now,
                "ship": ship_name,
                "location": location,
                "profit": profit,
            }
        )

    def print_ledger(self, ship_name: str):
        """Print complete transaction ledger for a specific ship.

        Displays all ledger entries from the ship's owning company
        cash account, showing timestamp, amount, running balance,
        and transaction memo.

        Args:
            ship_name: Name of ship (e.g., "Trader_001")

        Side Effects:
            Prints formatted ledger to stdout

        Raises:
            ValueError: If ship_name not found in agents list

        Example:
            >>> sim.print_ledger("Trader_001")
        """
        # Find the agent with matching ship name
        agent = None
        for a in self.agents:
            if a.ship.ship_name == ship_name:
                agent = a
                break

        if not agent:
            raise ValueError(
                f"Ship '{ship_name}' not found. "
                f"Available ships: {[a.ship.ship_name for a in self.agents]}"
            )

        company = agent.ship.owner
        print(f"\n{'='*80}")
        print(f"LEDGER FOR {company.name} ({ship_name})")
        print(f"Final Balance: Cr{company.balance:,.0f}")
        print(f"{'='*80}")
        print(f"{'Date':<15} {'Amount':>15} {'Balance':>15} {'Memo':<35}")
        print(f"{'-'*80}")

        for entry in company.cash.ledger:
            date_str = self.format_traveller_date(entry.time)
            print(
                f"{date_str:<15} "
                f"{entry.amount:>15,} "
                f"{entry.balance_after:>15,} "
                f"{entry.memo:<35}"
            )

        print(f"{'='*80}\n")

    def print_all_ledgers(self):
        """Print complete transaction ledgers for all ships.

        Iterates through all agents and prints each ship's complete
        ledger with all transactions from their owning company.

        Side Effects:
            Prints formatted ledgers to stdout for all ships

        Note:
            This can be very verbose for large simulations or long
            durations. Consider using print_ledger() for specific
            ships instead.

        Example:
            >>> sim.print_all_ledgers()
        """
        print(f"\n{'#'*80}")
        print("COMPLETE LEDGER DUMP - ALL SHIPS")
        print(f"{'#'*80}")

        for agent in self.agents:
            self.print_ledger(agent.ship.ship_name)


def run_simulation(
    map_file: str = "resources/t5_map.txt",
    ship_classes_file: str = "resources/t5_ship_classes.csv",
    num_ships: int = 10,
    duration_days: float = 365.0,
    verbose: bool = False,
    starting_year: int = 1104,
    starting_day: int = 360,
) -> Dict[str, Any]:
    """Convenience function to run a complete simulation.

    One-line setup and execution: loads game data, creates
    Simulation instance, and runs to completion. Handles all
    file loading and GameState initialization internally.

    Args:
        map_file: Path to world data file
                  (default: "resources/t5_map.txt")
        ship_classes_file: Path to ship classes CSV
                           (default: "resources/t5_ship_classes.csv")
        num_ships: Number of ships to simulate (default: 10)
        duration_days: Simulation duration in days, can be
                       fractional (default: 365.0)
        verbose: Print detailed status updates during simulation
                 (default: False)
        starting_year: Starting year in Traveller calendar
                       (default: 1104)
        starting_day: Starting day of year, 1-365 (default: 360)

    Returns:
        Simulation results dictionary with keys: duration_days,
        num_ships, total_voyages, cargo_sales, total_profit, ships

    Example:
        >>> results = run_simulation(num_ships=50,
        ...                          duration_days=1000,
        ...                          verbose=True)
        >>> print(f"Total profit: Cr{results['total_profit']:,.0f}")
    """
    from t5code import GameState as gs_module, T5World
    from t5code.GameState import GameState

    # Initialize game state
    game_state = GameState()
    raw_worlds = gs_module.load_and_parse_t5_map(map_file)
    raw_ships = gs_module.load_and_parse_t5_ship_classes(ship_classes_file)

    # Convert worlds to T5World objects
    game_state.world_data = T5World.load_all_worlds(raw_worlds)
    game_state.ship_classes = raw_ships

    # Create and run simulation
    sim = Simulation(game_state,
                     num_ships=num_ships,
                     duration_days=duration_days,
                     verbose=verbose,
                     starting_year=starting_year,
                     starting_day=starting_day)
    return sim.run()
