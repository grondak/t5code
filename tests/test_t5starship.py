import unittest
from T5Code.T5Starship import T5Starship, DuplicateItemError
from T5Code.T5ShipClass import T5ShipClass
from T5Code.T5NPC import T5NPC
from T5Code.GameState import *
from T5Code.T5Mail import T5Mail
from T5Code.T5Lot import T5Lot
from T5Code.T5World import T5World


class TestT5Starship(unittest.TestCase):
    """Tests for the class T5Starship"""

    def get_me_a_starship(self, name, world):
        test_ship_data = {
            "small": {
                "class_name": "small",
                "jump_rating": 1,
                "maneuver_rating": 2,
                "cargo_capacity": 10,
            },
            "large": {
                "class_name": "large",
                "jump_rating": 3,
                "maneuver_rating": 3,
                "cargo_capacity": 200,
            },
        }
        test_ship_class = T5ShipClass("small", test_ship_data["small"])
        return T5Starship(name, world, test_ship_class)

    def test_create_starship_with_name(self):
        starship = self.get_me_a_starship("Your mom", "Home")
        self.assertEqual(starship.shipName, "Your mom")
        self.assertEqual(
            starship.passengers,
            {"all": set(), "high": set(), "low": set(), "mid": set()},
        )
        self.assertEqual(starship.mail, {})
        self.assertEqual(starship.location, "Home")
        self.assertEqual(starship.crew, {})

    def test_hire_crew(self):  # Add crew to the ship
        starship = self.get_me_a_starship("Your mom", "Home")
        npc1 = T5NPC("Bob")
        with self.assertRaises(ValueError) as context:
            starship.hire_crew("a string", npc1)
        self.assertTrue("Invalid crew position." in str(context.exception))
        with self.assertRaises(TypeError) as context:
            starship.hire_crew("medic", "a something")
        self.assertTrue("Invalid NPC." in str(context.exception))
        starship.hire_crew("medic", npc1)
        self.assertEqual(starship.crew, {"medic": npc1})

    def test_onload_passenger(self):  # Add a passenger to a starship
        starship = self.get_me_a_starship("Titanic", "Southampton")
        with self.assertRaises(TypeError) as context:
            starship.onload_passenger("a string", "high")
        self.assertTrue("Invalid passenger type." in str(context.exception))
        npc1 = T5NPC("Bob")
        with self.assertRaises(ValueError) as context:
            starship.onload_passenger(npc1, "yourmom")
        self.assertTrue("Invalid passenger class." in str(context.exception))
        starship.onload_passenger(npc1, "high")
        self.assertSetEqual({npc1}, starship.passengers["high"])
        npc2 = T5NPC("Doug")
        starship.onload_passenger(npc2, "high")
        self.assertSetEqual({npc1, npc2}, starship.passengers["high"])
        with self.assertRaises(DuplicateItemError) as context:
            starship.onload_passenger(npc1, "high")
        self.assertTrue(
            "Cannot load same passenger Bob twice." in str(context.exception)
        )
        self.assertSetEqual({npc1, npc2}, starship.passengers["high"])
        self.assertEqual(npc1.location, starship.shipName)
        self.assertEqual(npc2.location, starship.shipName)

    def test_offload_passengers(self):  # Priority Offload High Passengers
        starship = self.get_me_a_starship("Pequod", "Nantucket")
        npc1 = T5NPC("Bob")
        starship.onload_passenger(npc1, "high")
        npc2 = T5NPC("Doug")
        starship.onload_passenger(npc2, "high")
        npc3 = T5NPC("Bill")
        starship.onload_passenger(npc3, "mid")
        npc4 = T5NPC("Ted")
        starship.onload_passenger(npc4, "low")
        self.assertSetEqual(starship.passengers["high"], {npc1, npc2})
        self.assertSetEqual(starship.passengers["mid"], {npc3})
        self.assertSetEqual(starship.passengers["low"], {npc4})
        offloadedPassengers = starship.offload_passengers("high")
        self.assertSetEqual(offloadedPassengers, {npc1, npc2})
        self.assertSetEqual(set(), starship.passengers["high"])
        self.assertEqual(npc1.location, starship.location)
        self.assertEqual(npc2.location, starship.location)
        with self.assertRaises(ValueError) as context:
            starship.offload_passengers("a something")
        self.assertTrue("Invalid passenger class." in str(context.exception))
        offloadedPassengers = starship.offload_passengers("mid")
        self.assertSetEqual(offloadedPassengers, {npc3})
        self.assertSetEqual(set(), starship.passengers["mid"])
        self.assertEqual(npc3.location, starship.location)
        npc5 = T5NPC("Bones")
        npc5.set_skill("medic", 45)
        starship.hire_crew("medic", npc5)
        offloadedPassengers = starship.offload_passengers("low")
        self.assertSetEqual(offloadedPassengers, {npc4})
        self.assertSetEqual(set(), starship.passengers["low"])
        self.assertEqual(npc4.location, starship.location)

    def test_set_course_for(self):
        MAP_FILE = "tests/t5_test_map.txt"
        GameState.world_data = T5World.load_all_worlds(load_and_parse_t5_map(MAP_FILE))
        starship = self.get_me_a_starship("Steamboat", "Rhylanor")
        starship.set_course_for("Jae Tellona")
        self.assertEqual(starship.destination(), "Jae Tellona")

    def test_onload_mail(self):
        MAP_FILE = "tests/t5_test_map.txt"
        GameState.world_data = T5World.load_all_worlds(load_and_parse_t5_map(MAP_FILE))
        starship = self.get_me_a_starship("Steamboat", "Rhylanor")
        mail = T5Mail("Rhylanor", "Jae Tellona", GameState)
        starship.onload_mail(mail)
        self.assertEqual((starship.get_mail())[mail.serial], mail)
        with self.assertRaises(ValueError) as context:
            for mail_number in range(6):
                mail = T5Mail("Rhylanor", "Jae Tellona", GameState)
                starship.onload_mail(mail)
        self.assertTrue("Starship mail locker size exceeded." in str(context.exception))

    def test_offload_mail(self):
        MAP_FILE = "tests/t5_test_map.txt"
        GameState.world_data = T5World.load_all_worlds(load_and_parse_t5_map(MAP_FILE))
        starship = self.get_me_a_starship("Steamboat", "Rhylanor")
        mail = T5Mail("Rhylanor", "Jae Tellona", GameState)
        starship.onload_mail(mail)
        starship.offload_mail()
        self.assertEqual(len(starship.get_mail().keys()), 0)
        with self.assertRaises(ValueError) as context:
            starship.offload_mail()
        self.assertTrue("Starship has no mail to offload.")

    def test_awaken_passenger(self):
        starship = self.get_me_a_starship("Steamboat", "Rhylanor")
        npc1 = T5NPC("Bones")
        npc1.set_skill("medic", 3)
        starship.hire_crew("medic", npc1)
        npc2 = T5NPC("Ted")
        starship.onload_passenger(npc2, "low")
        self.assertEqual(
            starship.awakenLowPassenger(npc2, npc1, roll_override_in=20), True
        )
        self.assertEqual(npc2.get_state(), "Alive")
        self.assertEqual(
            starship.awakenLowPassenger(npc2, npc1, roll_override_in=-20), False
        )
        self.assertEqual(npc2.get_state(), "Dead")

    def test_onload_lot(self):
        starship = self.get_me_a_starship("Steamboat", "Rhylanor")
        MAP_FILE = "tests/t5_test_map.txt"
        GameState.world_data = T5World.load_all_worlds(load_and_parse_t5_map(MAP_FILE))
        lot = T5Lot("Rhylanor", GameState)
        lot.mass = 5000  # tons
        # load something that isn't a lot
        with self.assertRaises(TypeError) as context:
            starship.onload_lot("a string", "cargo")
        self.assertTrue("Invalid lot type." in str(context.exception))
        # load something that isn't the right lotType specifier
        with self.assertRaises(ValueError) as context:
            starship.onload_lot(lot, "your mom")
        self.assertTrue("Invalid lot value." in str(context.exception))
        # load a lot that's too big
        with self.assertRaises(ValueError) as context:
            starship.onload_lot(lot, "cargo")
        self.assertTrue(
            "Lot will not fit in remaining space." in str(context.exception)
        )
        # load the lot as freight
        lot.mass = 5  # tons
        starship.onload_lot(lot, "freight")
        # validate the lot is in the ship
        self.assertTrue(lot in starship.get_cargo()["freight"])
        # try to load the same lot again as freight
        with self.assertRaises(ValueError) as context:
            starship.onload_lot(lot, "freight")
        self.assertTrue("Attempt to load same lot twice." in str(context.exception))
        # try to load the same lot again as cargo
        with self.assertRaises(ValueError) as context:
            starship.onload_lot(lot, "cargo")
        self.assertTrue("Attempt to load same lot twice." in str(context.exception))
        # make a new lot and load it as cargo
        lot2 = T5Lot("Rhylanor", GameState)
        lot2.mass = 5  # tons
        starship.onload_lot(lot2, "cargo")
        self.assertTrue(lot2 in starship.get_cargo()["cargo"])
        # make a lot to fill the space
        lot3 = T5Lot("Rhylanor", GameState)
        with self.assertRaises(ValueError) as context:
            starship.onload_lot(lot3, "cargo")
        self.assertTrue(
            "Lot will not fit in remaining space." in str(context.exception)
        )

    def test_offload_lot(self):
        # invalid serial number
        starship = self.get_me_a_starship("Steamboat", "Rhylanor")
        MAP_FILE = "tests/t5_test_map.txt"
        GameState.world_data = T5World.load_all_worlds(load_and_parse_t5_map(MAP_FILE))
        lot = T5Lot("Rhylanor", GameState)
        lot.mass = 5
        starship.onload_lot(lot, "cargo")
        lot2 = T5Lot("Rhylanor", GameState)
        lot2.mass = 5
        starship.onload_lot(lot2, "cargo")
        self.assertTrue(lot in starship.get_cargo()["cargo"])
        with self.assertRaises(ValueError) as context:
            starship.offload_lot("your mom", "cargo")
        self.assertTrue("Invalid lot serial number." in str(context.exception))
        # invalid lot specifier value
        with self.assertRaises(ValueError) as context:
            starship.offload_lot(lot.serial, "your mom")
        self.assertTrue("Invalid lot value." in str(context.exception))
        # lot serial not found in specified lot specifier
        with self.assertRaises(ValueError) as context:
            starship.offload_lot(lot.serial, "freight")
        self.assertTrue("Lot not found as specified type." in str(context.exception))
        # lot removed properly
        lot3 = starship.offload_lot(lot.serial, "cargo")
        isStillThere = False
        for lotIndex in starship.get_cargo()["cargo"]:
            if lotIndex.serial == lot3.serial:
                isStillThere = True
        self.assertEqual(lot.serial, lot3.serial)
        self.assertFalse(isStillThere)
        self.assertEqual(len(starship.get_cargo()["cargo"]), 1)

    def setUp(self):
        self.ship = self.get_me_a_starship("Steamboat", "Rhylanor")

    def test_initial_balance(self):
        self.assertEqual(self.ship.balance, 0.0)

    def test_credit_valid_amount(self):
        self.ship.credit(100)
        self.assertEqual(self.ship.balance, 100.0)

    def test_debit_valid_amount(self):
        self.ship.credit(200)
        self.ship.debit(50)
        self.assertEqual(self.ship.balance, 150.0)

    def test_credit_invalid_type(self):
        with self.assertRaises(TypeError):
            self.ship.credit("not money")

    def test_debit_invalid_type(self):
        with self.assertRaises(TypeError):
            self.ship.debit(None)

    def test_credit_negative_amount(self):
        with self.assertRaises(ValueError):
            self.ship.credit(-10)

    def test_debit_negative_amount(self):
        with self.assertRaises(ValueError):
            self.ship.debit(-5)

    def test_debit_insufficient_funds(self):
        self.ship.credit(50)
        with self.assertRaises(ValueError):
            self.ship.debit(100)


if __name__ == "__main__":
    unittest.main()
