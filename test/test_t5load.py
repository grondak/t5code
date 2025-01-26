import unittest, uuid
from T5Load import T5Load
from GameState import GameState
from T5World import T5World


class TestT5Load(unittest.TestCase):
    """Tests for the class T5Load"""
    
    def is_guid(self, string):
        try:
            uuid_obj = uuid.UUID(string, version=4)  # Specify the UUID version to validate
            return str(uuid_obj) == string.lower()  # Check normalized form matches input
        except ValueError:
            return False
        
    def test_value(self):
        with self.assertRaises(Exception) as context:
            GameState.world_data = None
            load = T5Load('Rhylanor', GameState)
        self.assertTrue('GameState.world_data has not been initialized!' in str(context.exception))
        MAP_FILE = 'test/t5_test_map.txt'
        GameState.world_data = T5World.load_all_worlds(GameState.load_and_parse_t5_map(MAP_FILE))
        load = T5Load('Rhylanor', GameState)
        self.assertEqual(3500, load.origin_value)
        
    def test_cargo_id(self):
        with self.assertRaises(Exception) as context:
            GameState.world_data = None
            load = T5Load('Rhylanor', GameState)
        self.assertTrue('GameState.world_data has not been initialized!' in str(context.exception))
        MAP_FILE = 'test/t5_test_map.txt'
        GameState.world_data = T5World.load_all_worlds(GameState.load_and_parse_t5_map(MAP_FILE))
        load = T5Load('Rhylanor', GameState)
        self.assertEqual('F-Hi 3500', load.load_id)
        
    def test_load_mass(self):
        MAP_FILE = 'test/t5_test_map.txt'
        GameState.world_data = T5World.load_all_worlds(GameState.load_and_parse_t5_map(MAP_FILE))
        load = T5Load('Rhylanor', GameState)
        self.assertGreater(load.mass, 0)
        
    def test_load_serial(self):
        MAP_FILE = 'test/t5_test_map.txt'
        GameState.world_data = T5World.load_all_worlds(GameState.load_and_parse_t5_map(MAP_FILE))
        load = T5Load('Rhylanor', GameState)
        self.assertTrue(self.is_guid(load.serial))
        
    def test_determine_sale_value_on(self):
        MAP_FILE = 'test/t5_test_map.txt'
        GameState.world_data = T5World.load_all_worlds(GameState.load_and_parse_t5_map(MAP_FILE))
        load = T5Load('Rhylanor', GameState)        
        sale_value = load.determine_sale_value_on('Jae Tellona', GameState)
        self.assertEqual(8500, sale_value)
    
    def test_buying_trade_class_effects(self):
        test_trade_classifications_table = {
            'Bob': 1000,
            'Doug': -500,
        }
        test_trade_classifications = 'Bob Doug'
        value = T5Load.determine_buying_trade_classifications_effects(test_trade_classifications, test_trade_classifications_table)
        self.assertEqual(500, value)  
        
    def test_selling_trade_class_effect(self):
        origin_trade_classifications = 'In'
        selling_goods_trade_classifications_table = {'In': 'Ag In'}
        MAP_FILE = 'test/t5_test_map.txt'
        GameState.world_data = T5World.load_all_worlds(GameState.load_and_parse_t5_map(MAP_FILE))
        load = T5Load('Rhylanor', GameState)
        marketWorld = GameState.world_data['Jae Tellona']
        adjustment = T5Load.determine_selling_trade_classifications_effects(marketWorld, origin_trade_classifications, selling_goods_trade_classifications_table)
        self.assertEqual(1000, adjustment)
    
    def test_load_costs(self):
        test_trade_classifications_table = {
            'Bob': 1000,
            'Doug': -500,
        }
        test_trade_classifications = 'Bob Doug'
        value = T5Load.determine_load_cost(test_trade_classifications, test_trade_classifications_table, 5)
        self.assertEqual(4000, value)
        
    def test_filter_trade_classifications(self):
        provided_trade_classifications = ''
        allowed_trade_classifications = ''
        answer = T5Load.filter_trade_classifications(provided_trade_classifications, allowed_trade_classifications)
        self.assertEqual('', answer)
        provided_trade_classifications = 'I like kittens'
        allowed_trade_classifications = ''
        answer = T5Load.filter_trade_classifications(provided_trade_classifications, allowed_trade_classifications)
        self.assertEqual('', answer)
        provided_trade_classifications = 'I like kittens'
        allowed_trade_classifications = 'I like kittens'
        answer = T5Load.filter_trade_classifications(provided_trade_classifications, allowed_trade_classifications)
        self.assertEqual({'I', 'like', 'kittens'}, set(answer.split()))       
        
if __name__ == '__main__':
    MAP_FILE = 't5_test_map.txt'
    GameState.world_data = T5World.load_all_worlds(GameState.load_and_parse_t5_map(MAP_FILE))
    unittest.main()