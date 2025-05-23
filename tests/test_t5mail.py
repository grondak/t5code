import pytest
from T5Code.T5Mail import T5Mail
from T5Code.GameState import *
from T5Code.T5World import T5World


def test_destination_is_less_important_than_origin():
    GameState.world_data = None
    with pytest.raises(Exception) as excinfo:
        T5Mail("Rhylanor", "Jae Tellona", GameState)
    assert "GameState.world_data has not been initialized!" in str(excinfo.value)

    MAP_FILE = "tests/t5_test_map.txt"
    GameState.world_data = T5World.load_all_worlds(load_and_parse_t5_map(MAP_FILE))
    with pytest.raises(Exception) as excinfo:
        T5Mail("Jae Tellona", "Rhylanor", GameState)
    assert "Destination World must be at least Importance-2 less than origin world" in str(
        excinfo.value
    )

    mail = T5Mail("Rhylanor", "Jae Tellona", GameState)
    assert mail.origin_importance >= (mail.destination_importance + 2)
