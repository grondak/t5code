# t5code

[![Tests](https://img.shields.io/badge/tests-509%20passing-brightgreen)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-99%25-brightgreen)](htmlcov/)
[![Statements](https://img.shields.io/badge/statements-1915%20%7C%2011%20missed-brightgreen)](htmlcov/)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**A Python framework for Traveller 5 starship operations and large-scale trade simulation.**

This monorepo contains two packages:
- **t5code**: Core library for T5 mechanics, world generation, trade, and ship operations
- **t5sim**: Discrete-event simulation engine using SimPy for multi-ship trade networks

Implements 50 years of Traveller game design. Scales from single-ship mechanics (testable, debuggable) to 150-ship networks running 150 days of simulated trade in 0.4 seconds.  It's been run for a network of 160,000 ships for a year and that takes about 40 minutes.

---

## Features

### Discrete-Event Simulation (t5sim)

- **SimPy-based concurrent multi-ship operations** - 150 ships trading simultaneously without polling loops
- **14-state starship FSM** - Complete merchant voyage cycle: DOCKED -> OFFLOADING -> SELLING_CARGO -> MAINTENANCE -> LOADING_FREIGHT -> LOADING_CARGO -> LOADING_MAIL -> LOADING_PASSENGERS -> LOADING_FUEL -> DEPARTING -> MANEUVERING_TO_JUMP -> JUMPING -> ARRIVING
- **Realistic time modeling** - Configurable state durations, discrete hour-by-hour tracking integrated with traditional Traveller calendar format [DDD.FF-YYYY]
- **Annual maintenance scheduling** with crew profit share
  - Each ship assigned random maintenance day (days 2-365)
  - Annual profit calculated and 10% distributed to crew before maintenance
  - 14-day maintenance period; ships with insufficient funds become "broke" and suspend operations
  - Military/specialized ships never actually run out of money (Cr1M emergency funding just before they go "broke.")
  - Maintenance costs: 1/1000th of ship cost
- **Refueling duration** - Realistic refueling times based on starport quality
  - Refueling duration (in hours) = nD6 where n = starport RefuelRate (A/B: 2D6, C/D: 4D6, E/X: 0D6)
  - Rolled at refuel time; duration influences when ship can depart
  - Integrated into state machine; ships wait out refueling before departure phase
  - Examples: Class A starport = 2D6 hours (2-12 hours), Class C = 4D6 hours (4-24 hours)

### Intelligent Ship Operations

- **Profit-aware routing** - Ships evaluate cargo opportunities at all reachable worlds
  - Priority 1: Worlds with positive cargo profit (randomly selected among them)
  - Priority 2: Any reachable world if no profitable routes available
  - Priority 3: Stay at current location if nothing in range
  - Ships exclude worlds where they cannot refuel (fuel compatibility rule)
- **Smart cargo purchasing** - Skips lots that would result in losses
- **Captain risk profiles** - Each captain has unique operational preferences
  - 60% standard captains: depart at 80% hold capacity
  - 30% moderate captains: vary between 70-90% capacity
  - 8% cautious captains: wait for 91-95% capacity
  - 2% aggressive captains: depart early at 65-69% capacity
- **Intelligent freight loading with "hope" mechanism**
  - Captain-specific risk tolerances above create varied behavior
  - "Hope" Counter resets when freight successfully loads
  - "Hope" Counter causes ships to depart when no cargos appear after a while
  - Ships stay longer at profitable ports, depart faster from poor ones
- **Skill-based crew payroll** - Salaries calculated from position skill requirements
  - Formula: 100 Cr × skill level (Pilot-2 earns 200 Cr, Engineer-3 earns 300 Cr)
  - Chief Engineer receives +1 skill level bonus
  - Payroll processed monthly (Days 002, 030, 058, etc.)
  - Presume ships are always fully-crewed
  - Simulation does not consider crew changeover but just abstracts crew members as "numbers" - the required skill is always available to the ship

### Fuel System with Equipment Constraints

- **Fuel compatibility spawn logic** - Ships spawn only at compatible starports
  - Ships without fuel processors (`can_refine_fuel=false`) only spawn at A/B starports with refined fuel
  - Ships with fuel processors (`can_refine_fuel=true`) can spawn at any starport
  - Prevents impossible situations (ship stranded at incompatible port)
- **Fuel-aware destination selection** - Ships never jump to worlds where they cannot refuel
  - Applied at both Priority 1 (profitable routes) and Priority 2 (fallback worlds)
  - Emergent behavior: Ships naturally seek compatible worlds
- **Realistic refueling costs** - Cr500/ton for jump fuel, Cr500/ton for operations fuel
- **Fuel tracking** - Detailed consumption during jumps and operations

### Complete Trade Economics

- **Double-entry accounting system** - Account, Ledger, and LedgerEntry classes
  - Immutable audit trail for all financial operations
  - Transaction history with Traveller date timestamps and counterparty tracking
  - Every transaction flows through owner company accounts
- **Cargo profitability evaluation** - Per-ton profit calculation: sale_value - purchase_price
- **Passenger revenue** - High/mid/low berth fares by world tech level
- **Mail contract income** - Per-bundle revenue
- **Comprehensive ledger reporting** - Full transaction history with memo tracking

```
################################################################################
COMPLETE LEDGER DUMP - ALL SHIPS
################################################################################

================================================================================
LEDGER FOR Trader_001 Inc (Trader_001, a Liner @ Knorbes/Regina (1807))
Ship Cost: MCr104.1
Final Balance: Cr1,492,140
================================================================================
Date                     Amount         Balance Memo
--------------------------------------------------------------------------------
360.00-1104         1,000,000.0     1,000,000.0 Initial capitalization
360.00-1104              10,000     1,010,000.0 Freight income: 10t from Alell
361.00-1104              13,000     1,023,000.0 Freight income: 13t from Alell
362.00-1104              12,000     1,035,000.0 Freight income: 12t from Alell
363.00-1104              12,000     1,047,000.0 Freight income: 12t from Alell
364.00-1104               9,000     1,056,000.0 Freight income: 9t from Alell
365.00-1104               6,000     1,062,000.0 Freight income: 6t from Alell
001.00-1105               8,000     1,070,000.0 Freight income: 8t from Alell
002.00-1105              -2,400     1,067,600.0 Crew payroll: 15 crew, Cr2,400 total (Month 1)
002.00-1105               6,000     1,073,600.0 Freight income: 6t from Alell
003.00-1105               9,000     1,082,600.0 Freight income: 9t from Alell
004.00-1105               8,000     1,090,600.0 Freight income: 8t from Alell
005.00-1105              13,000     1,103,600.0 Freight income: 13t from Alell
007.00-1105              10,000     1,113,600.0 High passage fare at Alell
007.00-1105              10,000     1,123,600.0 High passage fare at Alell
007.00-1105              10,000     1,133,600.0 High passage fare at Alell
007.00-1105              10,000     1,143,600.0 High passage fare at Alell
007.00-1105              10,000     1,153,600.0 High passage fare at Alell
007.00-1105              10,000     1,163,600.0 High passage fare at Alell
007.00-1105              10,000     1,173,600.0 High passage fare at Alell
007.00-1105              10,000     1,183,600.0 High passage fare at Alell
007.00-1105              10,000     1,193,600.0 High passage fare at Alell
007.00-1105               8,000     1,201,600.0 Mid passage fare at Alell
007.00-1105               8,000     1,209,600.0 Mid passage fare at Alell
007.00-1105               8,000     1,217,600.0 Mid passage fare at Alell
007.00-1105               8,000     1,225,600.0 Mid passage fare at Alell
007.00-1105               8,000     1,233,600.0 Mid passage fare at Alell
007.00-1105               8,000     1,241,600.0 Mid passage fare at Alell
007.00-1105               8,000     1,249,600.0 Mid passage fare at Alell
007.00-1105               8,000     1,257,600.0 Mid passage fare at Alell
007.00-1105               8,000     1,265,600.0 Mid passage fare at Alell
007.00-1105               1,000     1,266,600.0 Low passage fare at Alell
007.00-1105               1,000     1,267,600.0 Low passage fare at Alell
007.00-1105               1,000     1,268,600.0 Low passage fare at Alell
007.00-1105               1,000     1,269,600.0 Low passage fare at Alell
007.00-1105               1,000     1,270,600.0 Low passage fare at Alell
007.00-1105               1,000     1,271,600.0 Low passage fare at Alell
016.00-1105             -27,160     1,244,440.0 Crew profit share (10% of Cr271,600.0)
016.00-1105            -104,100     1,140,340.0 Annual maintenance (year 1105)
030.00-1105              -2,400     1,137,940.0 Crew payroll: 15 crew, Cr2,400 total (Month 2)
030.00-1105               5,000     1,142,940.0 Freight income: 5t from Knorbes
031.00-1105               8,000     1,150,940.0 Freight income: 8t from Knorbes
032.00-1105               8,000     1,158,940.0 Freight income: 8t from Knorbes
033.00-1105               6,000     1,164,940.0 Freight income: 6t from Knorbes    
034.00-1105              10,000     1,174,940.0 Freight income: 10t from Knorbes
035.00-1105              10,000     1,184,940.0 Freight income: 10t from Knorbes
036.00-1105               6,000     1,190,940.0 Freight income: 6t from Knorbes
037.00-1105               8,000     1,198,940.0 Freight income: 8t from Knorbes
038.00-1105               4,000     1,202,940.0 Freight income: 4t from Knorbes
039.00-1105               2,000     1,204,940.0 Freight income: 2t from Knorbes
040.00-1105               7,000     1,211,940.0 Freight income: 7t from Knorbes
041.00-1105               4,000     1,215,940.0 Freight income: 4t from Knorbes
042.00-1105               7,000     1,222,940.0 Freight income: 7t from Knorbes
043.00-1105               5,000     1,227,940.0 Freight income: 5t from Knorbes
044.00-1105               4,000     1,231,940.0 Freight income: 4t from Knorbes
045.00-1105               8,000     1,239,940.0 Freight income: 8t from Knorbes
047.00-1105              10,000     1,249,940.0 High passage fare at Knorbes
047.00-1105              10,000     1,259,940.0 High passage fare at Knorbes
047.00-1105              10,000     1,269,940.0 High passage fare at Knorbes
047.00-1105              10,000     1,279,940.0 High passage fare at Knorbes
047.00-1105              10,000     1,289,940.0 High passage fare at Knorbes
047.00-1105              10,000     1,299,940.0 High passage fare at Knorbes
047.00-1105              10,000     1,309,940.0 High passage fare at Knorbes
047.00-1105              10,000     1,319,940.0 High passage fare at Knorbes
047.00-1105               8,000     1,327,940.0 Mid passage fare at Knorbes
047.00-1105               8,000     1,335,940.0 Mid passage fare at Knorbes
047.00-1105               8,000     1,343,940.0 Mid passage fare at Knorbes
047.00-1105               8,000     1,351,940.0 Mid passage fare at Knorbes
047.00-1105               8,000     1,359,940.0 Mid passage fare at Knorbes
047.00-1105               8,000     1,367,940.0 Mid passage fare at Knorbes
047.00-1105               1,000     1,368,940.0 Low passage fare at Knorbes
047.00-1105               1,000     1,369,940.0 Low passage fare at Knorbes
047.00-1105               1,000     1,370,940.0 Low passage fare at Knorbes
047.00-1105               1,000     1,371,940.0 Low passage fare at Knorbes
047.00-1105             -90,000     1,281,940.0 Fuel purchase
057.00-1105               4,000     1,285,940.0 Freight income: 4t from Forboldn
058.00-1105              -2,400     1,283,540.0 Crew payroll: 15 crew, Cr2,400 total (Month 3)
058.00-1105               2,000     1,285,540.0 Freight income: 2t from Forboldn
059.00-1105               9,000     1,294,540.0 Freight income: 9t from Forboldn
060.00-1105               3,000     1,297,540.0 Freight income: 3t from Forboldn
061.00-1105               8,000     1,305,540.0 Freight income: 8t from Forboldn
062.00-1105               5,000     1,310,540.0 Freight income: 5t from Forboldn
063.00-1105               5,000     1,315,540.0 Freight income: 5t from Forboldn
064.00-1105               6,000     1,321,540.0 Freight income: 6t from Forboldn
065.00-1105               6,000     1,327,540.0 Freight income: 6t from Forboldn
066.00-1105               6,000     1,333,540.0 Freight income: 6t from Forboldn
067.00-1105               5,000     1,338,540.0 Freight income: 5t from Forboldn
068.00-1105               7,000     1,345,540.0 Freight income: 7t from Forboldn
069.00-1105               4,000     1,349,540.0 Freight income: 4t from Forboldn
070.00-1105               6,000     1,355,540.0 Freight income: 6t from Forboldn
071.00-1105               9,000     1,364,540.0 Freight income: 9t from Forboldn
072.00-1105              10,000     1,374,540.0 Freight income: 10t from Forboldn
073.00-1105              10,000     1,384,540.0 High passage fare at Forboldn
073.00-1105              10,000     1,394,540.0 High passage fare at Forboldn
073.00-1105              10,000     1,404,540.0 High passage fare at Forboldn
073.00-1105              10,000     1,414,540.0 High passage fare at Forboldn
073.00-1105              10,000     1,424,540.0 High passage fare at Forboldn
073.00-1105              10,000     1,434,540.0 High passage fare at Forboldn
073.00-1105               8,000     1,442,540.0 Mid passage fare at Forboldn
073.00-1105               8,000     1,450,540.0 Mid passage fare at Forboldn
073.00-1105               8,000     1,458,540.0 Mid passage fare at Forboldn
073.00-1105               8,000     1,466,540.0 Mid passage fare at Forboldn
073.00-1105               8,000     1,474,540.0 Mid passage fare at Forboldn
073.00-1105               8,000     1,482,540.0 Mid passage fare at Forboldn
073.00-1105               8,000     1,490,540.0 Mid passage fare at Forboldn
073.00-1105               8,000     1,498,540.0 Mid passage fare at Forboldn
073.00-1105               1,000     1,499,540.0 Low passage fare at Forboldn
073.00-1105               1,000     1,500,540.0 Low passage fare at Forboldn
073.00-1105               1,000     1,501,540.0 Low passage fare at Forboldn
073.00-1105               1,000     1,502,540.0 Low passage fare at Forboldn
073.00-1105               1,000     1,503,540.0 Low passage fare at Forboldn
073.00-1105               1,000     1,504,540.0 Low passage fare at Forboldn
073.00-1105               1,000     1,505,540.0 Low passage fare at Forboldn
073.00-1105               1,000     1,506,540.0 Low passage fare at Forboldn
073.00-1105             -90,000     1,416,540.0 Fuel purchase
083.00-1105              11,000     1,427,540.0 Freight income: 11t from Knorbes
084.00-1105               5,000     1,432,540.0 Freight income: 5t from Knorbes
085.00-1105               8,000     1,440,540.0 Freight income: 8t from Knorbes
086.00-1105              -2,400     1,438,140.0 Crew payroll: 15 crew, Cr2,400 total (Month 4)
086.00-1105               6,000     1,444,140.0 Freight income: 6t from Knorbes
087.00-1105               2,000     1,446,140.0 Freight income: 2t from Knorbes
088.00-1105               7,000     1,453,140.0 Freight income: 7t from Knorbes
089.00-1105               7,000     1,460,140.0 Freight income: 7t from Knorbes
090.00-1105               8,000     1,468,140.0 Freight income: 8t from Knorbes
091.00-1105               9,000     1,477,140.0 Freight income: 9t from Knorbes
092.00-1105               3,000     1,480,140.0 Freight income: 3t from Knorbes
093.00-1105               3,000     1,483,140.0 Freight income: 3t from Knorbes
094.00-1105               9,000     1,492,140.0 Freight income: 9t from Knorbes
================================================================================
```

### Multi-Ship Trade Network Simulation

- **Emergent trading behavior**
  - Ships self-organize into trade networks (~1/3 to 1/2 in transit at any moment)
  - Natural hub formation at economically important worlds
  - Dynamic equilibrium reached where profitable opportunities drive constant flux
  - No explicit "traffic control"—emerges from local profit incentives
- **Trade route tracking** and profit analysis per voyage
- **Statistics collection** - Voyage counts, sales, balances, fleet composition
- **Leaderboard filtering by ship role**
  - Only civilian ships appear in leaderboard rankings (military/specialized excluded for fairness)
  - Bailout advantage makes non-civilian ships non-competitive
  - If no civilian ships exist, leaderboard not printed
- **Weighted ship selection by role** with predefined proportions
  - All 3 roles: 70% civilian, 20% specialized, 10% military
  - Two roles: 80/20 or 70/30 splits
  - Within each role, ships selected by `frequency` weights from CSV
- **Startup validation** - Per-role frequency totals must equal 1.0; simulation stops if invalid
- **Worlds report** - End-of-simulation summary showing all worlds with ships docked or in transit
  - Displays planet UWP and trade classifications
  - Tracks ships in jump space separately
  - Provides ship accounting verification (docked + in-transit = total)

### Status Display & Reporting

- **Verbose ship status messages** - Full operational state at each event
  - Format: `[TIME] SHIP_NAME at LOCATION (STATE): company=BALANCE, hold (X/Y), fuel (J/J ops), cargo/freight/passengers/mail counts | ACTION`
  - Shows captain departure threshold and freight loading attempt counter
  - Displays reasoning for all destination selections
- **Destination selection transparency**
  - `picked destination 'WorldName' because it showed cargo profit of +CrX/ton`
  - `picked destination 'WorldName' randomly because no in-range system could buy cargo`
  - Ships exclude incompatible worlds automatically
- **Crew payroll reporting** - Monthly payroll deductions with crew count and total
- **Maintenance notifications** - Annual maintenance day trigger, costs, crew share amounts
- **Jump fuel consumption** - Fuel remaining after each interstellar jump
- **Complete ship startup announcements** - Ship class, starting location, annual maintenance day

### T5 Game Mechanics (t5code)

- **Universal World Profile (UWP)** parsing and lookup
- **Starport classification** - A through E and X starports
- **Trade classifications** - Agricultural, Industrial, Rich, Poor, etc.
- **Skill-based NPC crew** - With skill checks and task resolution
- **Double-entry accounting** - Auditable financial transactions
- **Mail and passenger systems** - High, mid, low berth classifications
- **World data network** - 439 worlds with trade data and classifications
- **Ship class definitions** - Scout, Free Trader, Far Trader, Fat Trader, Liner with full specs
- **Property-based API** - Clean, intuitive access to ship state
- **Company ownership integration** - All financial transactions flow through owner accounts

---

## Example: 150-Ship Simulation (150 Days)

Running 150 civilian ships for 150 days shows emergent behavior:

```
Simulation Results:
- Total voyages completed: 898
- Total profit: Cr94,557,054.00
- Simulation time: 0.40 seconds
- Average per ship: 6.0 voyages, Cr630,380 profit

Top 5 Ships by Balance:
  1. Trader_055, a Liner @ Nonym/Darrian (0321): Cr2,387,600 (7 voyages)
  2. Trader_022, a Free Trader @ Zamine/Darrian (0421): Cr2,265,800 (8 voyages)
  3. Trader_125, a Liner @ Enope/Regina (2205): Cr2,233,480 (6 voyages)
  4. Trader_109, a Far Trader @ Orcrist/Sword Worlds (1126): Cr2,165,400 (9 voyages)
  5. Trader_036, a Liner @ Ilium/Darrian (0426): Cr2,139,600 (7 voyages)

Bottom 5 Ships by Balance:
  1. Trader_017, a Scout @ Mithril/Sword Worlds (1628): Cr925,128 (9 voyages)
  2. Trader_085, a Scout @ Spirelle/Lunion (1927): Cr924,997 (9 voyages)
  3. Trader_020, a Scout @ Enlas-du/Cronor (0601): Cr923,600 (10 voyages)
  4. Trader_118, a Scout @ Focaline/Aramis (2607): Cr913,480 (10 voyages)
  5. Trader_078, a Scout @ Bronze/Sword Worlds (1627): Cr903,125 (8 voyages)

World Distribution:
- Ships docked at worlds: 108
- Ships in jump space: 42 (~28%)
- Total in simulation: 150
```

**Key Emergent Behaviors:**
1. **Constant Flux** - ~28-42 ships perpetually in transit. No rule mandates this; it emerges from profit-seeking behavior and refueling requirements. Ships that keep moving are most profitable.
2. **Hub Formation** - Zeycude (4 ships), Dojodo (4 ships), Leander (3 ships) naturally accumulate traffic. No traffic control coded; it's entirely from independent profit calculations converging.
3. **Role-based Returns** - Liners average higher absolute returns than Scouts, but Scouts complete more voyages with tighter margins. Different ship classes self-optimize to different strategies.

---

## Installation & Usage

### Setup

```bash
pip install -r requirements.txt
```

### Run a Simulation

```bash
# 10 civilian ships, 1 year (365 days), standard output
python -m t5sim.run --include-civilian

# 50 ships, 100 days, verbose output with all ledgers and world report
python -m t5sim.run --include-civilian --ships 50 --days 100 --verbose --ledger-all --worlds-report

# 5 ships each role (15 total), 365 days
python -m t5sim.run --include-civilian --include-military --include-specialized --ships 5 --days 365
```

### CLI Options

```
--ships SHIPS             Number of starships (default: 10)
--days DAYS               Simulation duration in days (default: 365)
--verbose, -v             Print detailed status updates during simulation
--ledger SHIP_NAME        Print ledger for specific ship
--ledger-all              Print ledgers for all ships
--include-civilian        Include civilian ships (Scout, Free Trader, etc.)
--include-military        Include military ships (Close Escort, Corsair, etc.)
--include-specialized     Include specialized ships (Safari Ship, Packet, Lab Ship)
--worlds-report           Print detailed report of all worlds and ship locations at end
--year YEAR               Starting year in Traveller calendar (default: 1104)
--day DAY                 Starting day of year, 1-365 (default: 360)
```

### Run Tests

```bash
# Full test suite with coverage
pytest --cov=src --cov-report=html tests/

# Specific test
pytest tests/test_t5sim/test_fuel_compatibility.py -v

# Coverage report
pytest --cov=src --cov-report=term-missing tests/
```

---

### Coverage
```

Name                               Stmts   Miss  Cover   Missing
----------------------------------------------------------------
src\t5code\GameState.py               35      0   100%
src\t5code\T5Basics.py                78      0   100%
src\t5code\T5Company.py               27      0   100%
src\t5code\T5Exceptions.py            38      0   100%
src\t5code\T5Finance.py               41      0   100%
src\t5code\T5Lot.py                   83      0   100%
src\t5code\T5Mail.py                  16      0   100%
src\t5code\T5NPC.py                   35      0   100%
src\t5code\T5RandomTradeGoods.py      88      0   100%
src\t5code\T5ShipClass.py             22      0   100%
src\t5code\T5Starship.py             336      0   100%
src\t5code\T5Tables.py                11      0   100%
src\t5code\T5World.py                 82      0   100%
src\t5sim\run.py                     150      1    99%   465
src\t5sim\simulation.py              277      3    99%   242, 838, 864
src\t5sim\starship_agent.py          544      7    99%   606, 720, 817, 1018, 1214, 1271, 1386
src\t5sim\starship_states.py          52      1    98%   275
----------------------------------------------------------------
TOTAL                               1915     12    99%
```

## Architecture

### t5code Package

Core game mechanics, world data, and ship operations. 100% test coverage.

```
t5code/
├── GameState.py          # World data and game state management
├── T5Basics.py           # Core rules (skill checks, damage, etc.)
├── T5Company.py          # Company and financial tracking
├── T5Finance.py          # Ledger and accounting system
├── T5Lot.py              # Cargo lot representation and pricing
├── T5Mail.py             # Mail contract system
├── T5NPC.py              # Crew and NPC definitions
├── T5RandomTradeGoods.py # Cargo generation and pricing
├── T5ShipClass.py        # Ship class definitions with specs
├── T5Starship.py         # Complete starship operations (100% coverage)
├── T5Tables.py           # Game tables (STARPORT_TYPES, POSITIONS, etc.)
├── T5World.py            # World data with UWP parsing
└── T5Exceptions.py       # Custom exceptions
```

### t5sim Package

Discrete-event simulation engine. 98-99% coverage.

```
t5sim/
├── run.py                # CLI entry point
├── simulation.py         # Simulation engine and world setup
├── starship_agent.py     # SimPy agent and state machine
├── starship_states.py    # State definitions and transitions
└── __init__.py
```

### Data Files

```
resources/
├── ships.csv             # Ship class definitions with frequency weights
├── t5_map.txt            # Trade map layout
├── t5_ship_classes.csv   # Extended ship specs (fuel, cargo, costs, etc.)
├── trade_goods_tables.json # Cargo pricing and availability
└── README.md             # Data documentation
```

---

## Test Suite

**509 passing tests, 99% coverage**

Coverage by module:
- t5code: 100% (all core mechanics fully tested)
- t5sim: 98-99% (simulation engine, state machine, agent behavior)
- Overall: 1,915 statements, 11 missed

Major test categories:
- **Trade mechanics** - Cargo pricing, profit calculations, lot generation
- **Ship operations** - Refueling, maintenance, crew payroll, departure logic
- **Fuel compatibility** - Spawn validation, destination filtering
- **Refueling duration** - Dice-rolled times by starport quality, duration calculation and storage
- **Financial tracking** - Ledger entries, accounting integrity, balance tracking
- **State machine** - All 14 state transitions, edge cases
- **Multi-ship simulation** - Concurrent operations, emergent behavior

Recent coverage improvements (January 2026):
- Fixed T5Starship.py line 1054 (fuel compatibility check) -> 100% ✓
- Added comprehensive refueling duration tests (19 tests)
- Fixed starship_agent.py crew profit share insufficient funds path (lines 560-564)
- Reduced uncovered lines from 18 -> 11

Run tests:
```bash
pytest tests/                                    # Run all tests
pytest --cov=src --cov-report=html tests/        # Generate HTML coverage report
pytest tests/test_t5sim/test_fuel_compatibility.py -v  # Test specific feature
```

---

## Implementation Notes

### Why This Simulator Works

1. **Faithful to T5 Rules** - Incentives copied directly from 50 years of playtested game design
2. **Emergent, Not Scripted** - No explicit traffic control, hub management, or fleet coordination. Behavior emerges from local profit decisions.
3. **Scalable** - Works identically at 1 ship or 150 ships. Same mechanics, same behavior quality.
4. **Auditable** - Double-entry accounting means every credit is traceable. No magic black boxes.
5. **Fast** - 150 ships × 150 days in 0.4 seconds. Enables rapid iteration and analysis.

### Design Decisions

- **SimPy for concurrency** - Avoids polling loops; events drive the simulation forward
- **Property-based state** - Ships expose their state through properties for clean read-only access
- **Fuel compatibility baked in** - Not a hack; enforced at spawn and destination selection
- **Ledger per company** - Maintains financial reality; ships are owned by companies with shared accounts
- **Captain personalities** - Small variance (65-95% departure threshold) creates surprising behavior diversity

### Known Limitations

- **No piracy/security** - All trade is safe. Could add risk-aware routing.
- **No port politics** - All worlds treat all ships equally. Could add faction preferences.
- **Fixed world data** - Worlds don't change over time. Could add economic simulation.
- **No ship upgrades** - Ships don't improve. Could add progression systems.
- **Fueling is a step** - Fueling /could/ start upon ship docking; this simulator presumes fueling is one of many sequential steps in a port call.

These are intentional scope boundaries, not bugs. The simulator is feature-complete for merchant trading operations.

---

## Project Status

**Feature-complete**. Core mechanics are solid. 509 tests passing. Emergent behavior validated.

The foundation is done. You can run this simulator, analyze the output, and get meaningful data about how merchant shipping networks self-organize under T5 rules.

---

## License

MIT License - See [LICENSE](LICENSE) file for details

---

## References

- **Traveller 5 Core Rulebook** - Rules source material
- **SimPy Documentation** - Discrete-event simulation framework
- **Traveller Community** - Ongoing rules clarification and discussion
