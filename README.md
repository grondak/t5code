# t5code

[![Tests](https://img.shields.io/badge/tests-478%20passing-brightgreen)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-99%25-brightgreen)](htmlcov/)
[![Statements](https://img.shields.io/badge/statements-1860%20%7C%2018%20missed-brightgreen)](htmlcov/)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**A Python framework for Traveller 5 starship operations and large-scale trade simulation.**

This monorepo contains two packages:
- **t5code**: Core library for T5 mechanics, world generation, trade, and ship operations
- **t5sim**: Discrete-event simulation engine using SimPy for multi-ship trade networks

Built for realistic simulation of merchant starship operations, trade economics, passenger transport, and interstellar commerce in the Traveller universe.

---

## What's New

- **Worlds Report** (`--worlds-report` flag) - end-of-simulation summary of ship locations
  - Displays all worlds with ships docked or in transit
  - Shows planet UPP and trade classifications for each world
  - Tracks ships in jump space separately
  - Provides ship accounting verification (docked + in-transit = total)
  - Useful for analyzing trade network coverage and identifying busy worlds
- **Ship location tracking** - records arrival, departure, and jump space transitions
  - `record_ship_arrival()`: moves ship from jump space to world
  - `record_ship_enter_jump()`: removes ship from world into jump space
  - `record_ship_exit_jump()`: moves ship from jump space to destination
  - Prevents duplicate entries in location lists
- **Leaderboard filtering by ship role** - fair ranking system for mixed-role simulations
  - Only **civilian ships** appear in Top/Bottom rankings (military and specialized excluded)
  - **Military and specialized ships** excluded from leaderboards to prevent unfair comparison
  - Bailout advantage makes military/specialized ships non-competitive with civilians
  - If **no civilian ships** exist in simulation, leaderboard not printed at all
  - Broke ships still displayed for visibility regardless of role
- **Weighted ship selection by role** with predefined proportions:
  - All 3 roles: 70% civilian, 20% specialized, 10% military
  - Two roles: 80/20 (civ+spec or civ+mil) or 70/30 (spec+mil)
  - Within each role, ships selected using `frequency` weights from CSV
- **Role filtering CLI flags**: `--include-civilian`, `--include-military`, `--include-specialized`
  - No flags → includes all roles with 70/20/10 proportions
  - Missing role in data → clear error during startup
- **Startup validation** for ship classes: per-role `frequency` totals must equal 1.0
  - Simulation stops with message like: `Frequency totals invalid: role 'civilian' sums to 0.80 (expected 1.00)`
- **Enhanced startup announcements**: Now display ship class, starting location, and annual maintenance day
- **Refactored setup() method**: Reduced cognitive complexity by extracting helper methods
- Coverage update: 478 tests, 99% overall coverage (t5code: 100%, t5sim: 98-99%)

## Features

### 🎯 Discrete-Event Simulation (t5sim)
- **SimPy-based simulation** with concurrent multi-ship operations
- **14-state starship FSM** (DOCKED → OFFLOADING → SELLING_CARGO → MAINTENANCE → LOADING_FREIGHT → ...)
- **Annual maintenance scheduling** - 2-week maintenance period triggered after selling cargo when maintenance day is reached
  - Each ship assigned random annual maintenance day (days 2-365, excluding holiday day 1)
  - Maintenance checked after SELLING_CARGO (after commercial transactions complete)
  - Annual profit calculated: current balance - last year's balance
  - **Crew profit share**: 10% of annual profit paid to crew before maintenance
  - 14-day maintenance period suspends all activities except crew payroll
  - Once-per-year enforcement (tracks last_maintenance_year)
  - **Maintenance costs**: 1/1000th of ship cost (e.g., MCr 100 ship costs Cr 100,000)
  - Ships with insufficient funds for crew share or maintenance become "broke" and suspend operations
  - Profit, crew share, and maintenance cost displayed during maintenance
- **Patron bailout system** - prevents military and specialized ships from going broke
  - **Military ships**: Receive Cr1,000,000 bailout from patron when about to go broke
  - **Specialized ships**: Receive Cr1,000,000 bailout from patron when about to go broke
  - **Civilian ships**: Go broke normally and suspend operations
  - Bailout recorded in ledger as "Patron bailout (Military/Specialized ship)" transaction
  - Ships resume operations immediately after bailout
- **Profit-aware routing** - ships evaluate destinations for cargo profitability
- **Smart cargo purchasing** - skips lots that would result in losses
- **Skill-based crew payroll** - monthly salaries calculated from position skill requirements
  - Salary formula: 100 Cr × skill level (Pilot-2 earns 200 Cr, Engineer-3 earns 300 Cr)
  - Chief Engineer receives +1 skill level bonus
  - Payroll processed on first day of each month (Days 002, 030, 058, etc.)
  - Ships with insufficient funds become "broke" and suspend operations
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
  - Role filtering flags: `--include-civilian`, `--include-military`, `--include-specialized`
    - If no flags are provided, all ship roles are included by default
    - If a requested role is not present in the ship classes file, execution fails with a clear error
  - Role frequency validation: per-role `frequency` totals must sum to 1.0
    - Validation runs at startup; the simulation stops with an error if invalid.
    - Example: `Frequency totals invalid: role 'civilian' sums to 0.80 (expected 1.00)`
- **Fair leaderboard ranking system**
  - Only **civilian ships** appear in Top/Bottom balance rankings (military/specialized excluded)
  - Ensures fair comparison when running mixed-role simulations
  - Rationale: Military and specialized ships receive Cr1,000,000 patron bailouts, giving them unfair advantage
  - If no civilian ships exist in simulation, leaderboard not printed
  - Broke ships still displayed separately for visibility (regardless of role)

### 🚀 Starship Operations (t5code)
- **Complete starship management** with cargo holds, passenger berths, and mail lockers
- **Jump range calculation** based on ship drive capability and hex distance
- **Profitable destination finding** - evaluate all reachable worlds for trade opportunities
- **Crew skill system** with position-based skill checks (Pilot, Engineer, Steward, Admin, etc.)
- **Skill-based crew salaries** - 100 Cr per skill level, with Chief Engineer bonus
- **Property-based API** for clean, intuitive access to ship state
- **Company ownership integration** - starships owned by trading companies
  - All financial transactions flow through owner company accounts
  - Ships reference owner via optional `owner` attribute (backward compatible)
  - Balance property automatically returns company balance when owner exists
  - Maintains legacy behavior for ships without owners
- **Double-entry accounting system** with Account, Ledger, and LedgerEntry classes
  - Transaction history with Traveller date timestamps and counterparty tracking
  - Immutable audit trail for all financial operations
  - Support for credits, debits, and inter-account transfers
  - Time parameter required for all transactions (enforces temporal ordering)
  - Keyword-only parameters ensure correct usage
- **Company management** with T5Company for multi-ship trading operations
  - Owner capital tracking and corporate accounting
  - Centralized cash management with ledger integration
  - Every ship transaction creates ledger entries with descriptive memos
  - Complete financial audit trail from ship operations

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
- **Streamlined crew** - Captain and specialized crew for ship operations
  - Captain is multi-skilled: Pilot, Trader, Steward, Admin, Liaison
  - Ships with Captain position ("0"): Captain handles piloting duties
  - Ships without Captain position: Pilot serves as captain with full authority
  - Additional crew: Engineer, Astrogator, Medic, Sensop, Freightmaster, etc.
  - All ships display captain's name and risk profile regardless of crew structure
- **Passenger classes** (High, Middle, Low passage)
- **Low passage survival mechanics** with medic skill effects

### 🎲 Game Mechanics
- **T5 dice mechanics** (2d6, flux, sequential flux)
- **Task resolution** with skill modifiers
- **Random trade goods** generation with classification-specific tables
- **Imbalance goods** with bonus opportunities
- **Imperial Calendar** with 13 months of 28 days plus Holiday
  - `TravellerCalendar` class for month calculations
  - Query current month from day of year
  - Get first day of any month or next month
  - Full integration with Traveller date format (DDD-YYYY)

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
from t5code import GameState, T5Starship, T5Company, T5World, T5Lot

# Initialize game data
game_state = GameState()
game_state.world_data = GameState.load_and_parse_t5_map("resources/t5_map.txt")
game_state.ship_classes = GameState.load_and_parse_t5_ship_classes("resources/t5_ship_classes.csv")

# Create a trading company
company = T5Company("Beowulf Trading Inc", starting_capital=1_000_000)

# Create a starship owned by the company
ship = T5Starship("Free Trader Beowulf", "A2", game_state, owner=company)

# Check company balance (ship transactions flow through company)
print(f"Company: {company.name}, Balance: Cr{company.balance:,.0f}")

# Load cargo (automatically debits company account with timestamp)
world = game_state.world_data["Regina"]
lot = T5Lot("Regina", game_state)
time = 0  # Simulation time (or use actual time in simulation)
ship.buy_cargo_lot(time, lot)

# Navigate to destination
ship.set_course_for("Efate")
print(f"Cargo manifest: {len(ship.cargo_manifest['cargo'])} lots")
print(f"Destination: {ship.destination}")
print(f"Company balance after purchase: Cr{company.balance:,.0f}")

# Sell cargo at destination (automatically credits company account with timestamp)
ship.sell_cargo_lot(time, lot, game_state)
print(f"Company balance after sale: Cr{company.balance:,.0f}")

# View complete transaction history with Traveller dates
for entry in company.cash.ledger:
    print(f"[{entry.time}] {entry.memo}: Cr{entry.amount:,.0f} (Balance: Cr{entry.balance_after:,.0f})")
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

**View all Adventure Class Ships:**
```bash
python examples/read_ship_classes.py
```

Displays all 15 Adventure Class Ships from T5 Core Rules with complete specifications:
- Scout, Free Trader, Far Trader, Fat Trader
- Close Escort, Gunned Escort, Liner, Safari Ship
- SDB, Packet, Mercenary Cruiser, Lab Ship
- Corsair, Corvette, Frigate

For each ship, shows:
- Ship cost (MCr), jump/maneuver/powerplant ratings
- Cargo capacity, staterooms, low berths
- **Decoded crew positions** (Captain, Pilot, Astrogator, Engineer, Medic, Steward, Freightmaster, Sensop, Cook, Gunner, Able Spacer, Spacer)
- Crew skill ranks
- Jump and ops fuel capacity

Additionally, this script validates role frequencies and reports any mismatches:
- Verifies that the sum of `frequency` values per `role` equals 1.0
- Prints a clear error if any role’s total is not 1.0 (e.g., "role 'civilian' sums to 0.80 (expected 1.00)")

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

# Print complete ledger for specific ship after simulation
python -m t5sim.run --ships 5 --days 45 --ledger Trader_001

# Print ledgers for all ships (verbose financial audit trail)
python -m t5sim.run --ships 3 --days 45 --ledger-all

# Print worlds report showing all worlds with docked/in-transit ships
python -m t5sim.run --ships 5 --days 30 --worlds-report

# Role-based filtering examples
# Only military ships
python -m t5sim.run --ships 10 --days 60 --include-military

# Civilian + specialized ships (uses 80% civilian, 20% specialized proportions)
python -m t5sim.run --ships 8 --days 45 --include-civilian --include-specialized

# All roles (uses 70% civilian, 20% specialized, 10% military proportions)
python -m t5sim.run --ships 20 --days 90 --include-civilian --include-military --include-specialized

# No role flags specified = all roles with default proportions (same as above)
python -m t5sim.run --ships 20 --days 90
```

Ship Selection & Role Proportions:
- When role flags are specified, ships are allocated using predefined proportions:
  - **All 3 roles** (or no flags): 70% civilian, 20% specialized, 10% military
  - **Civilian + Specialized**: 80% civilian, 20% specialized
  - **Civilian + Military**: 80% civilian, 20% military
  - **Specialized + Military**: 70% specialized, 30% military
  - **Single role**: 100% of that role
- Within each role, ships are selected using the `frequency` weights from `resources/t5_ship_classes.csv`
- Example: With `--ships 20` and all roles, expect ~14 civilian, ~4 specialized, ~2 military ships

Data validation:
- On startup, the CLI validates that per-role `frequency` values from `resources/t5_ship_classes.csv` sum to 1.0.
- If any role’s total differs from 1.0, the simulation stops with a clear error message.
- Example: `Frequency totals invalid: role 'civilian' sums to 0.80 (expected 1.00)`

**Verbose output example** (use `--verbose` flag to see detailed state transitions with Traveller date format DDD.FF-YYYY):
```
Trader_001 (Far Trader) starting simulation, cost: MCr44.1, destination: Ilium/Darrian (0426)
  Company: Trader_001 Inc, balance: Cr1,000,000
  Annual maintenance day: 292
  Crew: Captain: 80% Pilot-2, Astrogator: Astrogator-1, Engineer: Engineer-3, Medic: Medic-2, Steward: Steward-3
[360.00-1104] Trader_001 at Rorre/Darrian (0526) (DOCKED): company=Cr1,000,000, hold (0t/50.0t, 0%), 
  fuel (jump 40/40t, ops 4/4t), cargo=0 lots, freight=0 lots, passengers=(0H/0M/0L), mail=0 bundles
  Trader_001 (Far Trader) at Rorre: Jump-1, Cargo: 50.0t, Jump Fuel: 40/40t, Ops Fuel: 4/4t, Maint-Day: 292

[360.75-1104] Trader_001 at Rorre/Darrian (0526) (LOADING_FREIGHT): company=Cr1,003,000, hold (3t/50.0t, 6%), 
  fuel (jump 40/40t, ops 4/4t), cargo=0 lots, freight=1 lots, passengers=(0H/0M/0L), mail=0 bundles 
  | loaded 3t freight lot, income Cr3,000

[361.75-1104] Trader_001 at Rorre/Darrian (0526) (LOADING_FREIGHT): company=Cr1,008,000, hold (8t/50.0t, 16%), 
  fuel (jump 40/40t, ops 4/4t), cargo=0 lots, freight=2 lots, passengers=(0H/0M/0L), mail=0 bundles 
  | loaded 5t freight lot, income Cr5,000

[363.55-1104] Trader_002 at Prilissa/Trin's Veil (3035) (MANEUVERING_TO_JUMP): company=Cr1,000,000, 
  hold (0t/0.0t, 0%), fuel (jump 100/100t, ops 24/24t), cargo=0 lots, freight=0 lots, 
  passengers=(0H/0M/0L), mail=0 bundles | entering jump space to Murchison/Trin's Veil (2935)
Trader_002: Jumped 1 hexes, fuel remaining: 50/100t
[363.55-1104] Trader_002 at jump space (JUMPING): company=Cr1,000,000, hold (0t/0.0t, 0%), 
  fuel (jump 50/100t, ops 24/24t) | picked destination 'Pepernium' because it showed cargo profit of +Cr1900/ton 
  fuel (jump 180/180t, ops 18/18t), cargo=0 lots, freight=0 lots, passengers=(0H/0M/0L), mail=0 bundles | offloading complete

[360.75-1104] Trader_001 at Shirene/Lunion (2125) (SELLING_CARGO): company=Cr1,000,000, hold (0t/120.0t, 0%), 
  fuel (jump 180/180t, ops 18/18t), cargo=0 lots, freight=0 lots, passengers=(0H/0M/0L), mail=0 bundles | cargo sales complete

[360.75-1104] Trader_002 at Cipatwe/Rhylanor (3118) (LOADING_FREIGHT): company=Cr1,009,000, hold (9t/10.0t, 90%), 
  fuel (jump 20/20t, ops 2/2t), cargo=0 lots, freight=1 lots, passengers=(0H/0M/0L), mail=0 bundles | loaded 9t freight lot, income Cr9,000

[361.75-1104] Trader_001 at Shirene/Lunion (2125) (LOADING_FREIGHT): company=Cr1,005,000, hold (5t/120.0t, 4%), 
  fuel (jump 180/180t, ops 18/18t), cargo=0 lots, freight=1 lots, passengers=(0H/0M/0L), mail=0 bundles | loaded 5t freight lot, income Cr5,000

[361.75-1104] Trader_002 at Cipatwe/Rhylanor (3118) (LOADING_CARGO): company=Cr1,006,400, hold (10.0t/10.0t, 100%), 
  fuel (jump 20/20t, ops 2/2t), cargo=1 lots, freight=1 lots, passengers=(0H/0M/0L), mail=0 bundles | loaded 1 cargo lot(s), 1.0t total

[362.75-1104] Trader_001 at Shirene/Lunion (2125) (LOADING_FREIGHT): company=Cr1,005,000, hold (5t/120.0t, 4%), 
  fuel (jump 180/180t, ops 18/18t), cargo=0 lots, freight=1 lots, passengers=(0H/0M/0L), mail=0 bundles | hold only 4% full, need 80% (continuing freight loading, attempt 0.0)

[363.20-1104] Trader_002 at Cipatwe/Rhylanor (3118) (MANEUVERING_TO_JUMP): company=Cr1,006,400, hold (10.0t/10.0t, 100%), 
  fuel (jump 20/20t, ops 2/2t), cargo=1 lots, freight=1 lots, passengers=(0H/0M/0L), mail=0 bundles | entering jump space to Powaza/Rhylanor (3220)

[363.20-1104] Trader_002 at jump space (JUMPING): company=Cr1,006,400, hold (10.0t/10.0t, 100%), 
  fuel (jump 20/20t, ops 2/2t), cargo=1 lots, freight=1 lots, passengers=(0H/0M/0L), mail=0 bundles | picked destination 'Cipatwe' because it showed cargo profit of +Cr1900/ton

[005.20-1105] Trader_002 at jump space (JUMPING): company=Cr1,006,400, hold (10.0t/10.0t, 100%), 
  fuel (jump 0/20t, ops 2/2t), cargo=1 lots, freight=1 lots, passengers=(0H/0M/0L), mail=0 bundles | arrived at Powaza/Rhylanor (3220)

[006.05-1105] Trader_002 at Powaza/Rhylanor (3220) (OFFLOADING): company=Cr1,006,400, hold (1.0t/10.0t, 10%), 
  fuel (jump 0/20t, ops 2/2t), cargo=1 lots, freight=0 lots, passengers=(0H/0M/0L), mail=0 bundles | offloading complete

[006.05-1105] Trader_002 at Powaza/Rhylanor (3220) (SELLING_CARGO): company=Cr1,016,498, hold (0.0t/10.0t, 0%), 
  fuel (jump 0/20t, ops 2/2t), cargo=0 lots, freight=0 lots, passengers=(0H/0M/0L), mail=0 bundles | sold cargo lot for Cr7,498 profit

[006.05-1105] Trader_002 at Powaza/Rhylanor (3220) (MAINTENANCE): company=Cr1,016,498, hold (0.0t/10.0t, 0%), 
  fuel (jump 0/20t, ops 2/2t), cargo=0 lots, freight=0 lots, passengers=(0H/0M/0L), mail=0 bundles | annual profit: Cr16,498 (Cr1,000,000 to Cr1,016,498)

[006.05-1105] Trader_002 at Powaza/Rhylanor (3220) (MAINTENANCE): company=Cr1,014,848, hold (0.0t/10.0t, 0%), 
  fuel (jump 0/20t, ops 2/2t), cargo=0 lots, freight=0 lots, passengers=(0H/0M/0L), mail=0 bundles | crew profit share: Cr1,650 (10% of annual profit)

[006.05-1105] Trader_002 at Powaza/Rhylanor (3220) (MAINTENANCE): company=Cr986,278, hold (0.0t/10.0t, 0%), 
  fuel (jump 0/20t, ops 2/2t), cargo=0 lots, freight=0 lots, passengers=(0H/0M/0L), mail=0 bundles | undergoing annual maintenance (14 days), cost Cr28,570

[020.05-1105] Trader_002 at Powaza/Rhylanor (3220) (LOADING_FREIGHT): company=Cr986,278, hold (0.0t/10.0t, 0%), 
  fuel (jump 0/20t, ops 2/2t), cargo=0 lots, freight=0 lots, passengers=(0H/0M/0L), mail=0 bundles | no freight available
```

**Key verbose output features:**
- **Company balance tracking**: Shows `company=CrX,XXX,XXX` instead of `balance=` for owned ships
- **Company announcement at startup**: Displays company name and starting capital
- **Annual maintenance day**: Displayed at startup for each ship (e.g., "Annual maintenance day: 199")
- **Annual maintenance operations**: Triggered after SELLING_CARGO when maintenance day reached
  - Shows annual profit calculation: current balance - last year's balance
  - Example: "annual profit: Cr16,498 (Cr1,000,000 to Cr1,016,498)"
  - Crew receives 10% profit share before maintenance
  - Example: "crew profit share: Cr1,650 (10% of annual profit)"
  - Maintenance charged after crew profit share
  - Example: "undergoing annual maintenance (14 days), cost Cr28,570"
  - Ships with insufficient funds display: "insufficient funds for crew profit share" or "insufficient funds for annual maintenance"
  - Maintenance happens at most once per year, automatically tracks last_maintenance_year
- **Monthly crew payroll**: Ledger entries show skill-based salary calculations
  - Example: "Crew payroll: 7 crew, Cr1,900 total (Month 1)" for a Frigate
  - Payroll processed on day 002, 030, 058, etc. (first day of each month)
  - Ships with insufficient funds display: "insufficient funds for crew payroll (need CrX,XXX, have CrY,YYY), suspending operations"
- **Crew roster displayed at startup**: Shows all crew members with their skills
  - Format for captain: "Captain: X% Skill-Level" where X is cargo departure threshold
  - Format for crew: "Position: Skill-Level" or "Position N: Skill-Level" for multiple
  - Example (Scout): "Captain: 77% Pilot-2, Astrogator: Astrogator-2, Engineer: Engineer-3"
  - Example (Liner): Shows captain with separate pilot, plus all 15+ crew members
  - Ships with only Pilot display: "Captain: X% Pilot-Y" (pilot serves as captain)
  - Ships with Captain+Pilot display both separately with specialized roles
  - Ships with zero cargo capacity (Frigates): Display correctly, skip freight loading
- Ship class shown at startup (Scout, Freighter, Frigate, Liner)
- **Fuel status tracking**: Shows `fuel (jump X/Yt, ops A/Bt)` for both jump and operational fuel
  - Jump fuel depletes to 0/capacity after each jump, refills at port
  - Ops fuel typically stays full unless ship has extended operations
  - Example: `fuel (jump 180/180t, ops 18/18t)` for full Liner tanks
  - Example: `fuel (jump 0/20t, ops 2/2t)` for Scout after jump-2 transit
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
- Full status header: day, location, state, company/balance, hold capacity, fuel levels
- Single-line format with pipe separator for actions
- Financial tracking: income from freight/passengers, profit from cargo sales, monthly payroll
- Hold and fuel percentages help assess ship readiness at a glance
- State names match the action just completed

**Worlds Report** (`--worlds-report` flag):

Displays end-of-simulation summary of all worlds with docked or in-transit ships:

```bash
python -m t5sim.run --ships 3 --days 5 --worlds-report
```

Output example:
```
####################################################################################################
WORLDS REPORT - END OF SIMULATION
####################################################################################################

World                                UPP       Trade Classifications                  Ships  Ship Names
---------------------------------------------------------------------------------------------------------------------------------------------------------
Caladbolg/Sword Worlds(1329)         B565776-A Ag Ri                                  1      Trader_002
In jump space                                                                         2      Trader_001, Trader_003
---------------------------------------------------------------------------------------------------------------------------------------------------------

Ships docked at worlds: 1
Ships in jump space: 2
Total ships in simulation: 3
```

**Report features:**
- **Worlds with ships only**: Empty worlds are omitted from the report
- **Traveller-style format**: World names with sector and hex in parentheses (e.g., `Caladbolg/Sword Worlds(1329)`)
- **UPP and trade classifications**: Shows planet characteristics and trade classifications for each world
- **Ship tracking**: Lists ship names inline for easy reference
- **Jump space row**: Dedicated row tracks ships currently in transit between worlds
- **Ship accounting**: Summary lines verify all ships are accounted for (docked + in transit = total)
- **Useful for**: 
  - Verifying ship locations at simulation end
  - Identifying trade clusters and busy worlds
  - Tracking ships that got stuck in jump space
  - Validating multi-world coverage in trade networks

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
  1. Trader_003, a Frigate @ Nexine/Mora (3030): Cr5,892,340.00 (15 voyages)
  2. Trader_007, a Scout @ Tarsus/Trin's Veil (2826): Cr5,441,220.00 (14 voyages)
  ...

Bottom 5 ships by balance:
  1. Trader_008, a Liner @ Bronze/Lunion (1808): Cr3,441,220.00 (10 voyages)
  2. Trader_002, a Frigate @ Aster/Lanth (1807): Cr3,192,100.00 (9 voyages)
  ...

Broke ships (3):
  1. Trader_012, a Corsair @ Spume: Cr226,000.00 (18 voyages)
  2. Trader_015, a Packet @ Xhosa: Cr0.00 (34 voyages)
  3. Trader_019, a Mercenary Cruiser @ Vreibefger: Cr0.00 (25 voyages)
```

**Ship leaderboard features:**
- **Top 5 ships**: Best performing ships by final balance (excludes broke ships)
- **Bottom 5 ships**: Poorest performing active ships (excludes broke ships)
- **Broke ships**: Separate section for ships that ran out of funds during simulation
  - Shows count in header (e.g., "Broke ships (3)")
  - Ships that couldn't pay crew payroll or annual maintenance
  - Sorted by remaining balance (highest to lowest)
  - Only displayed if ships went broke during the simulation
- Dynamic grammar: "Top ship" vs "Top 5 ships", "Broke ship" vs "Broke ships (N)"
- Each entry shows: ship name, ship class, final location with sector/hex, balance, voyage count


**Complete ledger output (with --ledger or --ledger-all):**
```
================================================================================
LEDGER FOR Trader_001 Inc (Trader_001, a Scout @ Tarsus/Trin's Veil (2826))
Final Balance: Cr1,365,000
================================================================================
Date                     Amount         Balance Memo
--------------------------------------------------------------------------------
360.00-1104         1,000,000.0     1,000,000.0 Initial capitalization
360.00-1104               5,000     1,005,000.0 Freight income: 5t from Tarsus
360.00-1104               3,000     1,008,000.0 Freight income: 3t from Tarsus
360.00-1104              10,000     1,018,000.0 High passage fare at Tarsus
360.00-1104              10,000     1,028,000.0 High passage fare at Tarsus
360.00-1104               8,000     1,036,000.0 Mid passage fare at Tarsus
360.00-1104               1,000     1,037,000.0 Low passage fare at Tarsus
002.00-1105                -800     1,036,200.0 Crew payroll: 4 crew, Cr800 total (Month 1)
006.00-1105               7,000     1,043,200.0 Freight income: 7t from Avastan
017.00-1105              -3,600     1,039,600.0 Cargo purchase: 6-Ag Ni 3600 at Traltha
018.00-1105               6,120     1,045,720.0 Cargo sale: 6-Ag Ni 3600 at Traltha
030.00-1105                -800     1,044,920.0 Crew payroll: 4 crew, Cr800 total (Month 2)
199.00-1105              -4,572     1,040,348.0 Crew profit share (10% of Cr45,720)
199.00-1105             -28,570     1,011,778.0 Annual maintenance (year 1105)
...
================================================================================
```

**Key features:**
- **Ship context**: Ledger header shows company, ship name, ship class, and final location with hex
- **Traveller date format**: Shows exact simulation time (DDD.FF-YYYY) for each transaction
- **Complete audit trail**: Every credit, debit, and transfer with descriptive memo
- **Monthly payroll entries**: Shows crew count and total salary with month number
- **Annual profit share entries**: Shows 10% crew profit share with profit amount
- **Annual maintenance entries**: Shows maintenance cost (1/1000th of ship cost) with year
- **Running balance**: Balance after each transaction for easy verification
- **Transaction types**: Initial capital, freight income, passenger fares, cargo purchases/sales, crew payroll, crew profit share, maintenance costs
- **Location tracking**: Memos include world names where transactions occurred

---

## Project Structure

```
t5code/
├── src/
│   ├── t5code/              # Core library (100% coverage, all modules)
│   │   ├── T5Starship.py    # Starship operations with CrewPosition system
│   │   ├── T5World.py       # World generation with subsector/hex location formatting
│   │   ├── T5Lot.py         # Cargo lot mechanics
│   │   ├── T5NPC.py         # Character/crew system with cargo_departure_threshold
│   │   ├── T5Mail.py        # Mail contract system
│   │   ├── T5Finance.py     # Double-entry accounting system (Account, Ledger, LedgerEntry)
│   │   ├── T5Company.py     # Trading company with corporate accounting
│   │   ├── T5ShipClass.py   # Ship design specifications (4 classes: Scout, Freighter, Frigate, Liner)
│   │   ├── T5RandomTradeGoods.py  # Trade goods tables
│   │   ├── T5Basics.py      # Core game mechanics
│   │   ├── T5Tables.py      # Reference tables with sector name lookups and position codes
│   │   ├── T5Exceptions.py  # Custom exception hierarchy
│   │   └── GameState.py     # Global game state with sector mapping
│   └── t5sim/               # Simulation engine (99% coverage)
│       ├── starship_states.py   # 14-state FSM (98% coverage)
│       ├── starship_agent.py    # SimPy process agent (99% coverage)
│       ├── simulation.py        # Main orchestrator (100% coverage)
│       └── run.py               # CLI interface (98% coverage)
├── tests/
│   ├── test_t5code/         # Comprehensive tests for core library
│   └── test_t5sim/          # Simulation engine tests
├── examples/
│   ├── GameDriver.py        # Single-ship example
│   ├── sim.py              # Simulation example
│   └── read_ship_classes.py # Display all Adventure Class Ships
├── resources/               # Game data files
│   ├── t5_map.txt          # World data
│   └── t5_ship_classes.csv # Complete Adventure Class Ships from T5 Core Rules (15 ship types)
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
- **t5code**: All modules at 100% coverage
  - GameState.py, T5Basics.py, T5Company.py, T5Exceptions.py, T5Finance.py
  - T5Lot.py, T5Mail.py, T5NPC.py, T5RandomTradeGoods.py
  - T5ShipClass.py, T5Starship.py, T5Tables.py, T5World.py
- **t5sim**: All modules at 100% coverage
  - simulation.py: 100% coverage
  - starship_agent.py: 100% coverage
  - starship_states.py: 100% coverage
  - run.py: 100% coverage
- **Total**: 462 tests, 100% overall coverage (880 statements, 0 missed)

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
- ✅ **Captain/Pilot architecture** - flexible crew structure (Captain serves as pilot, or Pilot serves as captain)
- ✅ **Zero cargo capacity handling** - Frigates and other non-cargo ships operate correctly

---

## API Highlights

### Imperial Calendar

```python
from t5code.T5Basics import TravellerCalendar

cal = TravellerCalendar()

# Get month from day of year
month = cal.get_month(100)  # Returns 4
month = cal.get_month(1)    # Returns None (Holiday)

# Get first day of a month
first_day = cal.get_first_day_of_month(1)   # Returns 2
first_day = cal.get_first_day_of_month(13)  # Returns 338

# Get next month start
next_month = cal.get_next_month_start(15)   # Returns 30 (Month 2)
next_month = cal.get_next_month_start(365)  # Returns 2 (Month 1, next year)

# Get comprehensive info
info = cal.get_month_info(100)
# {'day': 100, 'month': 4, 'day_of_month': 15, 'is_holiday': False}

# Integration with Traveller dates
traveller_date = "180-1105"
day = int(traveller_date.split('-')[0])
info = cal.get_month_info(day)
print(f"Month {info['month']}, Day {info['day_of_month']}")
# Output: Month 7, Day 11
```

### Jump Range Calculation

```python
# Get worlds reachable by this ship's jump drive
reachable_worlds = ship.get_worlds_in_jump_range(game_state)

# Jump rating determines range (1-6 parsecs)
scout_company = T5Company("Scout Corp", starting_capital=1_000_000)
scout = T5Starship("Scout", "Rhylanor", scout_class, owner=scout_company)  # Jump-1
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
print(ship.balance)               # Credit balance (from owner company if owned)
print(ship.cargo_manifest)        # All cargo lots
print(ship.mail_bundles)          # Mail containers
```

### Financial Operations with Time Tracking

```python
from t5code import T5Company

# All financial transactions require time parameter for ledger
time = 360.0  # Simulation time (e.g., day 360 of year 1104)

# Direct credit/debit (ships with owner automatically use company ledger)
ship.credit(time, 50000, "Freight income: 50t from Regina")
ship.debit(time, 10000, "Port fees at Efate")

# Cargo operations (time parameter required)
ship.buy_cargo_lot(time, lot)  # Debits company account
result = ship.sell_cargo_lot(time, lot, game_state)  # Credits company account

# Freight and passengers (time parameter required)
ship.load_freight_lot(time, freight_lot)  # Credits freight income
ship.load_passengers(time, world)  # Credits passenger fares

# View transaction history with timestamps
for entry in ship.owner.cash.ledger:
    print(f"[{entry.time}] {entry.memo}: Cr{entry.amount:,.0f}")
```

### Skill-Based Operations

```python
# Crew skills affect outcomes
ship.hire_crew("steward", T5NPC("Jane", skills={"Steward": 2}))
ship.hire_crew("trader", T5NPC("Bob", skills={"Trader": 3}))

# Skills improve passenger bookings and cargo prices (time required)
time = 360.0
passengers = ship.load_passengers(time, world)
result = ship.sell_cargo_lot(time, lot, game_state, use_trader_skill=True)
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
- [x] Captain/Pilot flexible architecture with correct display formatting
- [x] Zero cargo capacity ship handling (Frigates operate without freight/cargo)
- [x] Company ownership integration with double-entry accounting
- [x] Complete financial audit trail through ledger system
- [x] Annual maintenance scheduling with 2-week downtime periods
 

---

## Contact

Questions? Issues? Contributions?  
Open an issue on GitHub or submit a pull request.