import unittest
from T5Starship import *
from T5NPC import *
from GameState import *
from T5Mail import *


class TestT5Starship(unittest.TestCase):
    """Tests for the class T5Starship"""

    def test_create_starship_with_name(self): # Make and Name a starship
        starship = T5Starship('Your mom', 'Home')
        self.assertEqual(starship.shipName, 'Your mom')
        self.assertEqual(starship.highPassengers, set())
        self.assertEqual(starship.mail, {})
        self.assertEqual(starship.location, 'Home')
    
    def test_onload_high_passenger(self): # Add a passenger to a starship
        starship = T5Starship('Titanic', 'Southampton')
        npc1 = T5NPC('Bob')
        starship.onload_high_passenger(npc1)
        self.assertSetEqual({npc1}, starship.highPassengers)
        npc2 = T5NPC('Doug')
        starship.onload_high_passenger(npc2)
        self.assertSetEqual({npc1, npc2}, starship.highPassengers)
        with self.assertRaises(DuplicateItemError) as context:
            starship.onload_high_passenger(npc1)
        self.assertTrue('Cannot load same passenger Bob twice.' in str(context.exception))
        self.assertSetEqual({npc1, npc2}, starship.highPassengers)
        self.assertEqual(npc1.location, starship.shipName)
        self.assertEqual(npc2.location, starship.shipName)
    
    def test_offload_high_passengers(self): # Priority Offload High Passengers
        starship = T5Starship('Pequod', 'Nantucket')
        npc1 = T5NPC('Bob')
        starship.onload_high_passenger(npc1)
        npc2 = T5NPC('Doug')
        starship.onload_high_passenger(npc2)
        self.assertSetEqual(starship.highPassengers, {npc1, npc2})
        offloadedPassengers = starship.offload_high_passengers()
        self.assertSetEqual(offloadedPassengers, {npc1, npc2})
        self.assertSetEqual(set(), starship.highPassengers)
        self.assertEqual(npc1.location, starship.location)
        self.assertEqual(npc2.location, starship.location)    
    
    def test_set_course_for(self):
        MAP_FILE = 'test/t5_test_map.txt'
        GameState.world_data = T5World.load_all_worlds(GameState.load_and_parse_t5_map(MAP_FILE))
        starship = T5Starship('Steamboat', 'Rhylanor')
        starship.set_course_for('Jae Tellona')
        self.assertEqual(starship.destination(), 'Jae Tellona')
    
    def test_onload_mail(self):
        MAP_FILE = 'test/t5_test_map.txt'
        GameState.world_data = T5World.load_all_worlds(GameState.load_and_parse_t5_map(MAP_FILE))
        starship = T5Starship('Steamboat', 'Rhylanor')
        mail = T5Mail('Rhylanor', 'Jae Tellona', GameState)
        starship.onload_mail(mail)
        self.assertEqual((starship.get_mail())[mail.serial], mail)
        with self.assertRaises(ValueError) as context:
            for mail_number in range(6):
                mail = T5Mail('Rhylanor', 'Jae Tellona', GameState)
                starship.onload_mail(mail)
        self.assertTrue('Starship mail locker size exceeded.' in str(context.exception))
    
    def test_offload_mail(self):
        MAP_FILE = 'test/t5_test_map.txt'
        GameState.world_data = T5World.load_all_worlds(GameState.load_and_parse_t5_map(MAP_FILE))
        starship = T5Starship('Steamboat', 'Rhylanor')
        mail = T5Mail('Rhylanor', 'Jae Tellona', GameState)
        starship.onload_mail(mail)
        starship.offload_mail()
        self.assertEqual(len(starship.get_mail().keys()), 0)
        with self.assertRaises(ValueError) as context:
            starship.offload_mail()
        self.assertTrue('Starship has no mail to offload.')
        
if __name__ == '__main__':
    unittest.main()