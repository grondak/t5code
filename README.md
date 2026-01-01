# t5code

[![Tests](https://img.shields.io/badge/tests-228%20passing-brightgreen)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)](htmlcov/)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**A Python framework for simulating Traveller 5 starship operations and interstellar trade.**

Built for discrete-event simulation of merchant starship operations, trade economics, and passenger transport in the Traveller universe. Features comprehensive world generation, cargo speculation, mail contracts, and crew skill systems.

---

## Features

### 🚀 Starship Operations
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

# Install package in editable mode
pip install -e .
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

---

## Project Structure

```
t5code/
├── src/t5code/          # Main package
│   ├── T5Starship.py    # Starship operations (241 statements)
│   ├── T5World.py       # World generation and trade
│   ├── T5Lot.py         # Cargo lot mechanics
│   ├── T5NPC.py         # Character/crew system
│   ├── T5Mail.py        # Mail contract system
│   ├── T5ShipClass.py   # Ship design specifications
│   ├── T5RandomTradeGoods.py  # Trade goods tables
│   ├── T5Basics.py      # Core game mechanics
│   ├── T5Tables.py      # Reference tables
│   ├── T5Exceptions.py  # Custom exception hierarchy
│   └── GameState.py     # Global game state
├── tests/               # 228 tests, 100% coverage
├── examples/
│   └── GameDriver.py    # Complete simulation example
├── resources/           # Game data files
│   ├── t5_map.txt       # World data
│   └── t5_ship_classes.csv  # Ship specifications
└── README.md
```

---

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests with coverage
pytest --cov=src/t5code --cov-report=term -q

# Generate HTML coverage report
pytest --cov=src/t5code --cov-report=html
# Open htmlcov/index.html in browser
```

**Current Status:** 228 tests passing, 100% code coverage (646 statements)

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
- 🔄 **Discrete-event simulation** integration (in progress)
- 🔄 **Multi-ship simulation** with SimPy (planned)

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
- [ ] SimPy integration for discrete-event simulation
- [ ] Multi-starship trade network simulation
- [ ] Jump route pathfinding
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