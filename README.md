# t5code

[![Tests](https://img.shields.io/badge/tests-309%20passing-brightgreen)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-99%25-brightgreen)](htmlcov/)
[![Statements](https://img.shields.io/badge/statements-1185%20%7C%2011%20missed-brightgreen)](htmlcov/)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**A Python framework for Traveller 5 starship operations and large-scale trade simulation.**

This monorepo contains two packages:
- **t5code**: Core library for T5 mechanics, world generation, trade, and ship operations
- **t5sim**: Discrete-event simulation engine using SimPy for multi-ship trade networks

Built for realistic simulation of merchant starship operations, trade economics, passenger transport, and interstellar commerce in the Traveller universe.

---

## Features

### 🎯 Discrete-Event Simulation (t5sim)
- **SimPy-based simulation** with concurrent multi-ship operations
- **12-state starship FSM** (DOCKED → OFFLOADING → SELLING_CARGO → LOADING_FREIGHT → ...)
- **Profit-aware routing** - ships evaluate destinations for cargo profitability
- **Smart cargo purchasing** - skips lots that would result in losses
- **Captain risk profiles** - each ship's captain has unique operational preferences
  - 60% standard captains depart at 80% hold capacity
  - 30% moderate captains vary between 70-90% capacity
  - 8% cautious captains wait for 91-95% capacity
  - 2% aggressive captains depart early at 65-69% capacity
- **Intelligent freight loading** with captain-specific departure thresholds
  - **"Hope" mechanism**: Counter resets each time freight is successfully loaded
  - Ships stay longer at profitable ports, depart faster from poor ones
  - Different captains exhibit different patience levels
- **Realistic time modeling** with configurable state durations
- **Trade route tracking** and profit analysis
- **Statistics collection** for voyages, sales, and balances
- **CLI interface** for easy simulation runs

### 🚀 Starship Operations (t5code)
- **Complete starship management** with cargo holds, passenger berths, and mail lockers
- **Jump range calculation** based on ship drive capability and hex distance
- **Profitable destination finding** - evaluate all reachable worlds for trade opportunities
- **Crew skill system** with position-based skill checks (Pilot, Engineer, Steward, Admin, etc.)
- **Property-based API** for clean, intuitive access to ship state
- **Financial tracking** with credit/debit operations and transaction validation

### 🌍 World System
- **T5 world generation** with UWP (Universal World Profile) support
- **Sector name lookup** - subsector codes mapped to full sector names (SECTORS table)
- **Trade classifications** (Agricultural, Industrial, Rich, Poor, etc.)
- **Starport quality** affecting broker availability and fees
- **Population-based** passenger and freight availability

### 📦 Trade & Economics
- **Speculative cargo** with origin-based lot generation
- **Dynamic pricing** using tech level differentials and trade code matching
- **Broker system** with skill-based price modifiers
- **Freight contracts** with standard tonnage-based payment
- **Mail contracts** for high-importance worlds

### 👥 NPCs & Passengers
- **Character skill system** with skill groups and skill levels
- **Captain risk profiles** - randomly generated operational personalities
  - Stored in `cargo_departure_threshold` attribute (0.60 to 0.98)
  - Influences when captains decide to depart port
  - Creates varied ship behaviors in simulations
  - Captain is multi-skilled: trader-2, steward-1, admin-1, liaison-1
- **Streamlined crew** - Captain handles all merchant operations, Medic for low passage
- **Passenger classes** (High, Middle, Low passage)
- **Low passage survival mechanics** with medic skill effects

### 🎲 Game Mechanics
- **T5 dice mechanics** (2d6, flux, sequential flux)
- **Task resolution** with skill modifiers
- **Random trade goods** generation with classification-specific tables
- **Imbalance goods** with bonus opportunities

---

## Quick Start

### Installation

```bash
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install core library only
pip install -e .

# Install with simulation support (includes SimPy)
pip install -e ".[simulation]"

# Install with all development tools
pip install -e ".[all]"
```

### Basic Example

```python
from t5code import GameState, T5Starship, T5World, T5Lot

# Initialize game data
game_state = GameState()
game_state.world_data = GameState.load_and_parse_t5_map("resources/t5_map.txt")
game_state.ship_classes = GameState.load_and_parse_t5_ship_classes("resources/t5_ship_classes.csv")

# Create a starship
ship = T5Starship("Free Trader Beowulf", "A2", game_state)
ship.credit(1_000_000)  # Starting capital

# Load cargo
world = game_state.world_data["Regina"]
lot = T5Lot("Regina", game_state)
ship.buy_cargo_lot(lot)

# Navigate to destination
ship.set_course_for("Efate")
print(f"Cargo manifest: {len(ship.cargo_manifest['cargo'])} lots")
print(f"Destination: {ship.destination}")
print(f"Balance: Cr{ship.balance:,.0f}")
```

### Running the Example Simulation

**Single-ship example:**
```bash
python examples/GameDriver.py
```

Output shows a complete trading voyage with passenger transport, cargo speculation, and financial tracking:

```
=== Jump to Dentus ===
Loaded 3 freight lots for Cr15,000
Loaded 2 high, 1 mid passengers (Cr19,000)
...
Balance: Cr1,045,230
```

**Multi-ship discrete-event simulation:**
```bash
# Quick test (5 ships, 30 days)
python -m t5sim.run --ships 5 --days 30

# Full year simulation (50 ships)
python -m t5sim.run --ships 50 --days 365

# Verbose mode - see detailed ship status at each state transition
python -m t5sim.run --ships 3 --days 30 --verbose

# Custom starting date (Traveller calendar format)
python -m t5sim.run --ships 5 --days 30 --year 1105 --day 1 --verbose
```

**Verbose output example (Traveller date format DDD.FF-YYYY with fractional days):**
```
Trader_001 (Liner) starting simulation, destination: Nosea/Darrian (0724)
  Crew: Captain: 80% trader-2 steward-1 admin-1 liaison-1, Medic: medic-1
[360.00-1104] Trader_001 at Enos/Sword Worlds (1130) (DOCKED): balance=Cr1,000,000, hold (0t/120.0t, 0%), 
  cargo=0 lots, freight=0 lots, passengers=(0H/0M/0L), mail=0 bundles

[360.25-1104] Trader_001 at Enos/J (1130) (OFFLOADING): balance=Cr1,000,000, hold (0t/120.0t, 0%), 
  cargo=0 lots, freight=0 lots, passengers=(0H/0M/0L), mail=0 bundles | offloading complete

[360.75-1104] Trader_001 at Enos/J (1130) (SELLING_CARGO): balance=Cr1,000,000, hold (0t/120.0t, 0%), 
  cargo=0 lots, freight=0 lots, passengers=(0H/0M/0L), mail=0 bundles | cargo sales complete

[361.75-1104] Trader_001 at Enos/J (1130) (LOADING_FREIGHT): balance=Cr1,004,000, hold (4t/120.0t, 3%), 
  cargo=0 lots, freight=1 lots, passengers=(0H/0M/0L), mail=0 bundles | loaded 4t freight lot, income Cr4,000

[362.75-1104] Trader_001 at Enos/J (1130) (LOADING_FREIGHT): balance=Cr1,004,000, hold (4t/120.0t, 3%), 
  cargo=0 lots, freight=1 lots, passengers=(0H/0M/0L), mail=0 bundles | hold only 3% full, need 80% (continuing freight loading, attempt 0.0)

[001.35-1105] Trader_001 at Enos/J (1130) (LOADING_PASSENGERS): balance=Cr679,000, hold (120.0t/120.0t, 100%), 
  cargo=1 lots, freight=4 lots, passengers=(7H/7M/0L), mail=0 bundles | loaded 7 high, 7 mid, 0 low passengers, income Cr126,000

[001.60-1105] Trader_001 at Enos/J (1130) (LOADING_PASSENGERS): balance=Cr679,000, hold (120.0t/120.0t, 100%), 
  cargo=1 lots, freight=4 lots, passengers=(7H/7M/0L), mail=0 bundles | loading complete, ready to depart

[002.10-1105] Trader_001 at Enos/J (1130) (DEPARTING): balance=Cr679,000, hold (120.0t/120.0t, 100%), 
  cargo=1 lots, freight=4 lots, passengers=(7H/7M/0L), mail=0 bundles | departing starport for Worldname/A (1234)

[002.60-1105] Trader_001 at Enos/J (1130) (MANEUVERING_TO_JUMP): balance=Cr679,000, hold (120.0t/120.0t, 100%), 
  cargo=1 lots, freight=4 lots, passengers=(7H/7M/0L), mail=0 bundles | entering jump space to Worldname/A (1234)

[002.60-1105] Trader_001 at jump space (JUMPING): balance=Cr679,000, hold (120.0t/120.0t, 100%), 
  cargo=1 lots, freight=4 lots, passengers=(7H/7M/0L), mail=0 bundles | picked destination 'Worldname' because it showed cargo profit of +Cr2000/ton

[009.60-1105] Trader_001 at jump space (JUMPING): balance=Cr679,000, hold (120.0t/120.0t, 100%), 
  cargo=1 lots, freight=4 lots, passengers=(7H/7M/0L), mail=0 bundles | arrived at Worldname/A (1234)

[010.10-1105] Trader_001 at Worldname/A (1234) (MANEUVERING_TO_PORT): balance=Cr679,000, hold (120.0t/120.0t, 100%), 
  cargo=1 lots, freight=4 lots, passengers=(7H/7M/0L), mail=0 bundles | docking at starport

[010.20-1105] Trader_001 at Worldname/A (1234) (OFFLOADING): balance=Cr679,000, hold (105.0t/120.0t, 88%), 
  cargo=1 lots, freight=0 lots, passengers=(0H/0M/0L), mail=0 bundles | offloading complete

[010.70-1105] Trader_001 at Worldname/A (1234) (SELLING_CARGO): balance=Cr682,135, hold (0.0t/120.0t, 0%), 
  cargo=0 lots, freight=0 lots, passengers=(0H/0M/0L), mail=0 bundles | sold cargo lot for Cr3,135 profit
```

**Key verbose output features:**
- **Crew roster displayed at startup**: Shows all NPCs with their skills
  - Format: "NPC Name: threshold% skill-level skill-level"
  - Example: "Captain: 80% trader-2 steward-1 admin-1 liaison-1, Medic: medic-1"
  - Captain shows cargo departure threshold percentage followed by all skills
  - Streamlined 2-person crew (Captain + Medic) handles all operations
- Ship class shown at startup (e.g., Scout, Freighter, Liner, Corvette)
- **Traveller date format**: `[DDD.FF-YYYY]` format with fractional days for hour-by-hour tracking
  - Examples: `[360.00-1104]` (day start), `[360.25-1104]` (6 hours), `[360.75-1104]` (18 hours)
- **Year rollover**: Automatically transitions from day 365 to day 001 of next year
- **Location format** includes sector name and hex: `WorldName/Sector (Hex)` 
  - Examples: `Fornice/Mora (3025)`, `Faisal/Querion (0518)`, `Rhylanor/Rhylanor (2716)`
  - Sector names are looked up from the SECTORS table using subsector codes
- **Jump space display**: Shows `at jump space (JUMPING)` during transit instead of destination
- **Destination selection reasoning**: Shows why each destination was picked:
  - `picked destination 'WorldName' because it showed cargo profit of +CrX/ton`
  - `picked destination 'WorldName' randomly because no in-range system could buy cargo`
- **Freight loading progress**: Shows captain's departure threshold and attempt counter
  - Displays captain's cargo_departure_threshold (e.g., "need 80%" or "need 85%")
  - `attempt 0.0` when freight obtained (hope mechanism active)
  - Counter increments only on failed attempts, captain gives up at 1.0 (4 cycles)
  - Different captains have different thresholds (65%-95% range)
- Full status header: day, location, state, balance, hold capacity with percentage
- Single-line format with pipe separator for actions
- Financial tracking: income from freight/passengers, profit from cargo sales
- Hold percentage helps assess cargo capacity at a glance
- State names match the action just completed

**Aggregate statistics output:**
```
======================================================================
SIMULATION RESULTS
======================================================================
Total voyages completed: 127
Total cargo sales: 1,854
Total profit: Cr45,231,920.00
Simulation time: 2.34 seconds (10 ships, 365.0 days)

Average per ship:
  Voyages: 12.7
  Profit: Cr4,523,192.00

Top 5 ships by balance:
  1. Trader_003: Cr5,892,340.00 (15 voyages)
  2. Trader_007: Cr5,441,220.00 (14 voyages)
  ...

Bottom 5 ships by balance:
  1. Trader_008: Cr3,441,220.00 (10 voyages)
  2. Trader_002: Cr3,192,100.00 (9 voyages)
  ...
```

---

## Project Structure

```
t5code/
├── src/
│   ├── t5code/              # Core library (235 tests, 100% coverage)
│   │   ├── T5Starship.py    # Starship operations
│   │   ├── T5World.py       # World generation with subsector/hex location formatting
│   │   ├── T5Lot.py         # Cargo lot mechanics
│   │   ├── T5NPC.py         # Character/crew system
│   │   ├── T5Mail.py        # Mail contract system
│   │   ├── T5ShipClass.py   # Ship design specifications
│   │   ├── T5RandomTradeGoods.py  # Trade goods tables
│   │   ├── T5Basics.py      # Core game mechanics
│   │   ├── T5Tables.py      # Reference tables with sector name lookups
│   │   ├── T5Exceptions.py  # Custom exception hierarchy
│   │   └── GameState.py     # Global game state with sector mapping
│   └── t5sim/               # Simulation engine (74 tests, 99% coverage)
│       ├── starship_states.py   # 12-state FSM
│       ├── starship_agent.py    # SimPy process agent (99% coverage)
│       ├── simulation.py        # Main orchestrator (100% coverage)
│       └── run.py               # CLI interface
├── tests/
│   ├── test_t5code/         # 235 tests for core library
│   └── test_t5sim/          # 74 tests for simulation
├── examples/
│   ├── GameDriver.py        # Single-ship example
│   └── sim.py              # Simulation example
├── resources/               # Game data files
│   ├── t5_map.txt          # World data
│   └── t5_ship_classes.csv # Ship specifications
└── README.md
```

---

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest tests/ -v

# Run t5code tests only
pytest tests/test_t5code/ -v

# Run t5sim tests only
pytest tests/test_t5sim/ -v

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=src --cov-report=html
# Open htmlcov/index.html in browser
```

**Current Status:**
- **t5code**: 235 tests passing, 100% coverage (includes sector lookup tests)
- **t5sim**: 74 tests passing, 97-98% coverage by module
  - simulation.py: 97% coverage (114 statements, 3 missed)
  - starship_agent.py: 98% coverage (274 statements, 5 missed)
  - starship_states.py: 98% coverage (50 statements, 1 missed)
- **Total**: 309 tests, 99% overall coverage (1185 statements, 11 missed)

### Code Quality

```bash
# Format code with black
pip install black
black .

# Run type checking (optional)
pip install mypy
mypy src/
```

### Project Goals

- ✅ **Complete T5 trade mechanics** with cargo speculation
- ✅ **Passenger transport system** with class-based pricing
- ✅ **Mail contracts** for X-boat network simulation
- ✅ **Crew skill system** with position-based modifiers
- ✅ **Custom exception hierarchy** for error handling
- ✅ **Property-based API** for clean state access
- ✅ **100% test coverage** with comprehensive test suite
- ✅ **Professional documentation** with Google-style docstrings
- ✅ **Discrete-event simulation** with SimPy integration
- ✅ **Multi-ship simulation** with state machines and statistics
- ✅ **Captain risk profiles** with varied operational personalities
- ✅ **Intelligent freight loading** with hope mechanism
- ✅ **Sector name mapping** for readable world locations

---

## API Highlights

### Jump Range Calculation

```python
# Get worlds reachable by this ship's jump drive
reachable_worlds = ship.get_worlds_in_jump_range(game_state)

# Jump rating determines range (1-6 parsecs)
scout = T5Starship("Scout", "Rhylanor", scout_class)  # Jump-1
print(f"Jump-{scout.jump_rating} can reach {len(reachable_worlds)} worlds")

# Automatically filters by:
# - Hex distance (Traveller formula)
# - Ship's jump rating
# - Travel zones (excludes Amber/Red)

# Example: Compare different ship capabilities
jump1_reach = jump1_ship.get_worlds_in_jump_range(game_state)
jump3_reach = jump3_ship.get_worlds_in_jump_range(game_state)
print(f"Jump-3 reaches {len(jump3_reach) - len(jump1_reach)} more worlds")
```

### Exception Handling

```python
from t5code import InsufficientFundsError, CapacityExceededError

try:
    ship.buy_cargo_lot(expensive_lot)
except InsufficientFundsError as e:
    print(f"Need Cr{e.required:,.0f}, have Cr{e.available:,.0f}")
except CapacityExceededError as e:
    print(f"Need {e.required}t, have {e.available}t {e.capacity_type}")
```

### Property Access

```python
# Clean, intuitive property-based API
print(ship.destination)           # Current destination world
print(ship.balance)               # Credit balance
print(ship.cargo_manifest)        # All cargo lots
print(ship.mail_bundles)          # Mail containers
```

### Skill-Based Operations

```python
# Crew skills affect outcomes
ship.hire_crew("steward", T5NPC("Jane", skills={"Steward": 2}))
ship.hire_crew("trader", T5NPC("Bob", skills={"Trader": 3}))

# Skills improve passenger bookings and cargo prices
passengers = ship.load_passengers(world)
result = ship.sell_cargo_lot(lot, game_state, use_trader_skill=True)
```

---

## Documentation

All modules feature comprehensive Google-style docstrings:

- **Module docstrings** explain purpose and contents
- **Class docstrings** detail attributes and usage
- **Method docstrings** specify Args, Returns, Raises, and Examples
- **T5 rules references** included where applicable

Generate documentation:

```bash
pip install pdoc3
pdoc --html --output-dir docs src/t5code
```

---

## License & Attribution

**The Traveller game in all forms is owned by Far Future Enterprises.**  
Copyright 1977 – 2024 Far Future Enterprises.  
[Traveller Fair Use Policy](https://cdn.shopify.com/s/files/1/0609/6139/0839/files/Traveller_Fair_Use_Policy_2024.pdf?v=1725357857)

This software is provided under the MIT License for the implementation code.  
Game mechanics and content are used under the Traveller Fair Use Policy.

---

## Contributing

Contributions welcome! This project follows:
- **TDD** (Test-Driven Development) - write tests first
- **100% coverage** - all code must be tested
- **Black formatting** - consistent code style
- **Type hints** - improve code clarity
- **Comprehensive docstrings** - document all public APIs

---

## Roadmap

### Near Term
- [x] SimPy integration for discrete-event simulation
- [x] Multi-starship trade network simulation
- [x] Profit-aware route planning with destination evaluation
- [x] Smart cargo purchasing (skip unprofitable lots)
- [x] Jump range validation and reachability checking
- [x] Sector name lookup table (SECTORS) for subsector code mapping
- [x] Captain risk profiles with varied operational personalities
- [x] Intelligent freight loading with hope mechanism
- [ ] Enhanced statistics and visualization
- [ ] Advanced pathfinding with multi-jump routes
- [ ] Ship maintenance and repair mechanics

### Long Term
- [ ] Complete subsector generation
- [ ] Economic modeling with supply/demand
- [ ] Piracy and conflict mechanics
- [ ] Character generation system
- [ ] Save/load simulation state

---

## Contact

Questions? Issues? Contributions?  
Open an issue on GitHub or submit a pull request.