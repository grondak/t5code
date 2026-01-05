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
import random
import simpy
from t5code import T5NPC
from t5code.GameState import GameState
from t5code.T5Starship import T5Starship
from t5sim.starship_agent import StarshipAgent
from t5sim.starship_states import StarshipState


def generate_captain_risk_profile() -> float:
    """Generate cargo departure threshold based on captain risk profile.

    Creates realistic distribution of captain behavior:
    - 60% chance: Standard (0.80) - cautious but practical
    - 30% chance: Moderate (0.70-0.90) - normal variance
    - 8% chance: Very cautious (0.91-0.95) - waits for full holds
    - 2% chance: Aggressive (0.65-0.69) - leaves early for speed

    Range is constrained to 0.60-0.98 to ensure reasonable behavior.

    Returns:
        Float between 0.60 and 0.98 representing cargo fill threshold

    Example:
        >>> threshold = generate_captain_risk_profile()
        >>> 0.60 <= threshold <= 0.98
        True
    """
    roll = random.random()

    if roll < 0.60:
        # 60% chance: Standard threshold
        return 0.80
    elif roll < 0.90:
        # 30% chance: Moderate range (70-90%)
        return random.uniform(0.70, 0.90)
    elif roll < 0.98:
        # 8% chance: Very cautious (91-95%)
        return random.uniform(0.91, 0.95)
    else:
        # 2% chance: Aggressive (65-69%)
        return random.uniform(0.65, 0.69)


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

            # Create actual ship
            ship = T5Starship(
                f"Trader_{i + 1:03d}", starting_world, ship_class
            )
            ship.credit(self.starting_capital)

            # Add basic crew
            self._add_basic_crew(ship)

            # Pick initial destination using same logic as agent's
            # _choose_next_destination(): prefer profitable routes
            if reachable_worlds:
                # First, try to find profitable destinations
                profitable = ship.find_profitable_destinations(
                    self.game_state
                )
                if profitable:
                    # Choose randomly from profitable destinations
                    destination, _ = random.choice(profitable)
                    ship.set_course_for(destination)
                else:
                    # No profitable destinations, pick any reachable
                    destination = random.choice(reachable_worlds)
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

    def _add_basic_crew(self, ship: T5Starship):
        """Add crew NPCs to fill all positions defined by the ship class.

        Creates NPCs for each position slot in ship.crew_position.
        Captain gets special treatment with random risk profile.
        Skills will be assigned later based on position requirements.

        Args:
            ship: T5Starship to crew
        """
        # Fill each position slot with an NPC
        for position_name, position_list in ship.crew_position.items():
            for i, crew_position in enumerate(position_list):
                # Generate unique name for multiple positions
                if len(position_list) > 1:
                    npc_name = f"{position_name} {i+1}"
                else:
                    npc_name = position_name

                # Create NPC
                npc = T5NPC(npc_name)

                # Special handling for Captain: add risk profile
                if position_name == "Captain":
                    npc.cargo_departure_threshold = generate_captain_risk_profile()

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
