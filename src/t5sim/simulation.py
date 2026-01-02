"""Main SimPy simulation orchestrator.

Manages the discrete-event simulation of multiple merchant starships
using t5code for game mechanics.
"""

from typing import List, Dict, Any
import simpy
from t5code import T5NPC
from t5code.GameState import GameState
from t5code.T5Starship import T5Starship
from t5sim.starship_agent import StarshipAgent
from t5sim.starship_states import StarshipState


class Simulation:
    """Main simulation controller for merchant starship operations.

    Attributes:
        env: SimPy environment
        game_state: GameState with world and ship data
        agents: List of active StarshipAgent instances
        statistics: Collected simulation data
    """

    def __init__(
        self,
        game_state: GameState,
        num_ships: int = 10,
        duration_days: float = 365.0,
        starting_capital: float = 1_000_000.0,
        speculate_cargo_pct: float = 1.0,
        verbose: bool = False,
    ):
        """Initialize the simulation.

        Args:
            game_state: Initialized GameState with world and ship data
            num_ships: Number of starships to simulate
            duration_days: Simulation duration in days
            starting_capital: Starting capital per ship in credits
            speculate_cargo_pct: Percentage of ships
               that speculate on cargo (0.0-1.0)
            verbose: Whether to print detailed status updates during simulation
        """
        self.env = simpy.Environment()
        self.game_state = game_state
        self.num_ships = num_ships
        self.duration_days = duration_days
        self.starting_capital = starting_capital
        self.speculate_cargo_pct = speculate_cargo_pct
        self.verbose = verbose

        self.agents: List[StarshipAgent] = []
        self.statistics: Dict[str, List[Any]] = {
            "cargo_sales": [],  # List of sale transactions
            "ship_balances": [],  # Periodic balance snapshots
            "trade_routes": [],  # Route usage tracking
        }

    def setup(self):
        """Create starships and agents."""
        import random
        from t5code import T5ShipClass

        worlds = list(self.game_state.world_data.keys())
        ship_classes_data = list(self.game_state.ship_classes.values())

        for i in range(self.num_ships):
            # Pick random starting world and ship class
            starting_world = random.choice(worlds)
            ship_class_dict = random.choice(ship_classes_data)

            # Convert dict to T5ShipClass object
            class_name = ship_class_dict["class_name"]
            ship_class = T5ShipClass(class_name, ship_class_dict)

            # Create ship
            ship = T5Starship(
                f"Trader_{i + 1:03d}", starting_world, ship_class
            )
            ship.credit(self.starting_capital)

            # Add basic crew
            self._add_basic_crew(ship)

            # Pick initial destination
            destination = random.choice(
                [w for w in worlds if w != starting_world]
            )
            ship.set_course_for(destination)

            # Determine if this ship speculates on cargo
            speculate = i < int(self.num_ships * self.speculate_cargo_pct)

            # Create agent
            agent = StarshipAgent(
                self.env, ship, self,
                starting_state=StarshipState.DOCKED,
                speculate_cargo=speculate
            )
            self.agents.append(agent)

    def _add_basic_crew(self, ship: T5Starship):
        """Add basic crew with skills to a ship.

        Args:
            ship: T5Starship to crew
        """
        # Trader
        trader = T5NPC("Trader")
        trader.set_skill("trader", 2)
        ship.hire_crew("trader", trader)

        # Steward
        steward = T5NPC("Steward")
        steward.set_skill("steward", 1)
        ship.hire_crew("steward", steward)

        # Admin
        admin = T5NPC("Admin")
        admin.set_skill("admin", 1)
        ship.hire_crew("admin", admin)

        # Liaison
        liaison = T5NPC("Liaison")
        liaison.set_skill("liaison", 1)
        ship.hire_crew("liaison", liaison)

        # Medic
        medic = T5NPC("Medic")
        medic.set_skill("medic", 1)
        ship.hire_crew("medic", medic)

    def run(self) -> Dict[str, Any]:
        """Run the simulation.

        Returns:
            Dictionary of simulation results and statistics
        """
        print(f"Setting up simulation with {self.num_ships} ships...")
        self.setup()

        print(f"Running simulation for {self.duration_days} days...")
        self.env.run(until=self.duration_days)

        print("Simulation complete. Generating results...")
        return self._generate_results()

    def _generate_results(self) -> Dict[str, Any]:
        """Generate summary results from simulation.

        Returns:
            Dictionary with simulation statistics
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

    def record_cargo_sale(self, ship_name: str, location: str, profit: float):
        """Record a cargo sale transaction.

        Args:
            ship_name: Name of ship making sale
            location: World where sale occurred
            profit: Profit/loss from sale
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
    speculate_cargo_pct: float = 1.0,
    verbose: bool = False,
) -> Dict[str, Any]:
    """Convenience function to run a complete simulation.

    Args:
        map_file: Path to world data file
        ship_classes_file: Path to ship classes CSV
        num_ships: Number of ships to simulate
        duration_days: Simulation duration in days
        speculate_cargo_pct: Percentage of ships that
          speculate on cargo (0.0-1.0)
        verbose: Whether to print detailed status updates during simulation

    Returns:
        Simulation results dictionary
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
                     speculate_cargo_pct=speculate_cargo_pct,
                     verbose=verbose)
    return sim.run()
