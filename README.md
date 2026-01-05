# t5code

[![Tests](https://img.shields.io/badge/tests-287%2B%20passing-brightgreen)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-99%25-brightgreen)](htmlcov/)
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
- **Realistic time modeling** with configurable state durations
- **Trade route tracking** and profit analysis
- **Statistics collection** for voyages, sales, and balances
- **CLI interface** for easy simulation runs

### 🚀 Starship Operations (t5code)
- **Complete starship management** with cargo holds, passenger berths, and mail lockers
- **Crew skill system** with position-based skill checks (Pilot, Engineer, Steward, Admin, etc.)
- **Property-based API** for clean, intuitive access to ship state
- **Financial tracking** with credit/debit operations and transaction validation

### 🌍 World System
- **T5 world generation** with UWP (Universal World Profile) support
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
- **Passenger classes** (High, Middle, Low passage)
- **Low passage survival mechanics** with medic skill effects
- **Crew position management** with role-based assignments

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

# No-speculation policy (80% of ships avoid cargo speculation)
python -m t5sim.run --ships 20 --days 365 --no-speculation 0.8
```

**Verbose output example:**
```
Trader_001 (Scout) starting simulation
[Day 0.0] Trader_001 at Sting (DOCKED): balance=Cr1,000,000, hold (0t/10.0t, 0%), 
  cargo=0 lots, freight=0 lots, passengers=(0H/0M/0L), mail=0 bundles

[Day 0.2] Trader_001 at Sting (OFFLOADING): balance=Cr1,000,000, hold (0t/10.0t, 0%), 
  cargo=0 lots, freight=0 lots, passengers=(0H/0M/0L), mail=0 bundles | offloading complete

[Day 0.8] Trader_001 at Sting (SELLING_CARGO): balance=Cr1,000,000, hold (0t/10.0t, 0%), 
  cargo=0 lots, freight=0 lots, passengers=(0H/0M/0L), mail=0 bundles | cargo sales complete

[Day 0.8] Trader_001 at Sting (LOADING_FREIGHT): balance=Cr1,008,000, hold (8t/10.0t, 80%), 
  cargo=0 lots, freight=1 lots, passengers=(0H/0M/0L), mail=0 bundles | loaded 8t freight lot, income Cr8,000

[Day 1.8] Trader_001 at Sting (LOADING_FREIGHT): balance=Cr1,008,000, hold (8t/10.0t, 80%), 
  cargo=0 lots, freight=1 lots, passengers=(0H/0M/0L), mail=0 bundles | hold only 80% full, need 80% (continuing freight loading, attempt 0.25)

[Day 2.6] Trader_001 at Sting (LOADING_PASSENGERS): balance=Cr1,008,000, hold (10.0t/10.0t, 100%), 
  cargo=0 lots, freight=1 lots, passengers=(0H/0M/0L), mail=0 bundles | loading complete, ready to depart

[Day 2.7] Trader_001 at Sting (DEPARTING): balance=Cr1,008,000, hold (10.0t/10.0t, 100%), 
  cargo=0 lots, freight=1 lots, passengers=(0H/0M/0L), mail=0 bundles | departing starport

[Day 3.2] Trader_001 at Sting (MANEUVERING_TO_JUMP): balance=Cr1,008,000, hold (10.0t/10.0t, 100%), 
  cargo=0 lots, freight=1 lots, passengers=(0H/0M/0L), mail=0 bundles | entering jump space

[Day 10.2] Trader_001 at Dentus (JUMPING): balance=Cr1,008,000, hold (10.0t/10.0t, 100%), 
  cargo=0 lots, freight=1 lots, passengers=(0H/0M/0L), mail=0 bundles | arrived at Dentus

[Day 10.7] Trader_001 at Dentus (MANEUVERING_TO_PORT): balance=Cr1,008,000, hold (10.0t/10.0t, 100%), 
  cargo=0 lots, freight=1 lots, passengers=(0H/0M/0L), mail=0 bundles | docking at starport

[Day 10.8] Trader_001 at Dentus (ARRIVING): balance=Cr1,008,000, hold (10.0t/10.0t, 100%), 
  cargo=0 lots, freight=1 lots, passengers=(0H/0M/0L), mail=0 bundles | docked and ready for business
```

**Key verbose output features:**
- Ship class shown at startup (e.g., Scout, Freighter, Liner)
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
│   ├── t5code/              # Core library (229 tests, 100% coverage)
│   │   ├── T5Starship.py    # Starship operations
│   │   ├── T5World.py       # World generation and trade
│   │   ├── T5Lot.py         # Cargo lot mechanics
│   │   ├── T5NPC.py         # Character/crew system
│   │   ├── T5Mail.py        # Mail contract system
│   │   ├── T5ShipClass.py   # Ship design specifications
│   │   ├── T5RandomTradeGoods.py  # Trade goods tables
│   │   ├── T5Basics.py      # Core game mechanics
│   │   ├── T5Tables.py      # Reference tables
│   │   ├── T5Exceptions.py  # Custom exception hierarchy
│   │   └── GameState.py     # Global game state
│   └── t5sim/               # Simulation engine (58 tests, 99% coverage)
│       ├── starship_states.py   # 12-state FSM
│       ├── starship_agent.py    # SimPy process agent
│       ├── simulation.py        # Main orchestrator
│       └── run.py               # CLI interface
├── tests/
│   ├── test_t5code/         # 229 tests for core library
│   └── test_t5sim/          # 58 tests for simulation
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
- **t5code**: 229 tests passing, 100% coverage
- **t5sim**: 58 tests passing, 99% coverage
- **Total**: 287 tests, 99% overall coverage

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

---

## API Highlights

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
- [ ] Intelligent route planning (currently random)
- [ ] Enhanced statistics and visualization
- [ ] Jump route pathfinding optimization
- [ ] Crew experience/advancement system
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