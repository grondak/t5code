"""Display captain risk profiles for a set of ships."""

import pytest
from t5code.GameState import (
    GameState,
    load_and_parse_t5_map,
    load_and_parse_t5_ship_classes,
)
from t5code.T5World import T5World
from t5sim.simulation import Simulation

game_state = GameState()
raw_worlds = load_and_parse_t5_map('resources/t5_map.txt')
raw_ships = load_and_parse_t5_ship_classes('resources/t5_ship_classes.csv')
game_state.world_data = T5World.load_all_worlds(raw_worlds)
game_state.ship_classes = raw_ships  # Used as dicts in simulation

sim = Simulation(game_state, num_ships=10, duration_days=1, verbose=False)
sim.setup()

print('Captain Risk Profiles:')
for i, agent in enumerate(sim.agents, 1):
    captain = agent.ship.crew.get('captain')
    threshold = captain.cargo_departure_threshold if captain else 0.8

    if threshold == pytest.approx(0.80):
        risk = 'STANDARD'
    elif threshold > 0.90:
        risk = 'CAUTIOUS'
    elif threshold < 0.70:
        risk = 'AGGRESSIVE'
    else:
        risk = 'MODERATE'

    print(f'  Ship {i}: {threshold:.1%} threshold ({risk})')
