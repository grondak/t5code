import uuid
from t5code.T5Basics import check_success
from t5code.T5Lot import T5Lot
from t5code.T5NPC import T5NPC
from t5code.T5ShipClass import T5ShipClass

INVALID_PASSENGER_CLASS_ERROR = "Invalid passenger class."
INVALID_CREW_POSITION_ERROR = "Invalid crew position."


class DuplicateItemError(Exception):
    """Custom exception for duplicate set items."""

    pass


class _BestCrewSkillDict:
    def __init__(self, crew_dict):
        self.crew = crew_dict

    def __getitem__(self, skill_name):
        skill_name = skill_name.lower()
        return max(
            (member.get_skill(skill_name) for member in self.crew.values()),
            default=0
        )


class T5Starship:
    """A starship class intended to implement just enough of the
    T5 Starship concepts to function in the simulator"""

    def __init__(self, ship_name, ship_location, ship_class: T5ShipClass):
        # Core identity
        self.ship_name = ship_name
        self.location = ship_location
        self.hold_size = ship_class.cargo_capacity

        # Passenger system
        self.high_passengers = set()
        self.passengers = {
            "high": set(),
            "mid": set(),
            "low": set(),
            "all": set(),  # useful for global queries or summary stats
        }

        # Mail, crew, and cargo tracking
        self.mail = {}  # mail_id → T5Mail object
        self.crew = {}  # role → T5NPC or crew record
        self.cargo = {
            "freight": [],  # freight lots
            "cargo": [],  # miscellaneous or special cargo
        }
        self.cargo_size = 0  # total tons of cargo on board
        self.mail_locker_size = 1  # max number of mail containers

        # Navigation
        self.destination_world = None  # assigned when a flight plan is set
        # Financials
        self._balance = 0.0  # in credits (millions, thousands — your scale)

    def set_course_for(self, destination):
        self.destination_world = destination

    def destination(self):
        return self.destination_world

    def onload_passenger(self, npc, passage_class):
        if not (isinstance(npc, T5NPC)):
            raise TypeError("Invalid passenger type.")
        ALLOWED_PASSAGE_CLASSES = ["high", "mid", "low"]
        if passage_class not in ALLOWED_PASSAGE_CLASSES:
            raise ValueError(INVALID_PASSENGER_CLASS_ERROR)
        if npc in self.passengers["all"]:
            error_result = "Cannot load same passenger " + \
                f"{npc.character_name} twice."
            raise DuplicateItemError(error_result)
        self.passengers["all"].add(npc)
        self.passengers[passage_class].add(npc)
        npc.location = self.ship_name

    def offload_passengers(self, passage_class):
        offloaded_passengers = set()
        allowed_passage_classes = {"high", "mid", "low"}

        if passage_class not in allowed_passage_classes:
            raise ValueError(INVALID_PASSENGER_CLASS_ERROR)

        for npc in set(self.passengers[passage_class]):
            if passage_class == "low":
                self.awaken_low_passenger(
                    npc,
                    self.crew.get("medic"),
                )
            npc.location = self.location
            self.passengers[passage_class].remove(npc)
            self.passengers["all"].remove(npc)
            offloaded_passengers.add(npc)

        return offloaded_passengers

    def awaken_low_passenger(self,
                             npc: T5NPC,
                             medic,
                             roll_override_in: int = None):
        if check_success(roll_override=roll_override_in,
                         skills_override=medic.skills):
            return True
        else:
            npc.kill()
            return False

    def onload_mail(self, mail_item):
        if len(self.mail.keys()) >= self.mail_locker_size:
            raise ValueError("Starship mail locker size exceeded.")
        self.mail[mail_item.serial] = mail_item

    def offload_mail(self):
        if len(self.mail.keys()) == 0:
            raise ValueError("Starship has no mail to offload.")
        self.mail = {}

    def get_mail(self):
        return self.mail

    def hire_crew(self, position, npc: T5NPC):
        ALLOWED_CREW_POSITIONS = ["medic", "crew1", "crew2", "crew3"]
        if position not in ALLOWED_CREW_POSITIONS:
            raise ValueError("Invalid crew position.")
        if not (isinstance(npc, T5NPC)):
            raise TypeError("Invalid NPC.")
        self.crew[position] = npc

    @property
    def best_crew_skill(self):
        return _BestCrewSkillDict(self.crew)

    ALLOWED_LOT_TYPES = {"cargo", "freight"}

    def can_onload_lot(self, in_lot, lot_type):
        if not isinstance(in_lot, T5Lot):
            raise TypeError("Invalid lot type.")

        if lot_type not in self.ALLOWED_LOT_TYPES:
            raise ValueError("Invalid lot value.")

        if in_lot.mass + self.cargo_size > self.hold_size:
            raise ValueError("Lot will not fit in remaining space.")

        if in_lot in self.cargo["freight"] or in_lot in self.cargo["cargo"]:
            raise ValueError("Attempt to load same lot twice.")

        return True  # explicitly returns True if all checks pass

    def onload_lot(self, in_lot, lot_type):
        if self.can_onload_lot(in_lot, lot_type):
            self.cargo[lot_type].append(in_lot)
            self.cargo_size += in_lot.mass

    def offload_lot(self, in_serial: uuid, lot_type):
        try:
            uuid.UUID(in_serial)
        except ValueError:
            raise ValueError("Invalid lot serial number.")
        if not ((lot_type == "cargo") or (lot_type == "freight")):
            raise ValueError("Invalid lot value.")
        result = next((lot for lot in self.cargo[
            lot_type] if lot.serial == in_serial), None)

        if result is None:
            raise ValueError("Lot not found as specified type.")
        else:
            self.cargo[lot_type].remove(result)
            self.cargo_size -= result.mass
            return result

    def get_cargo(self):
        return self.cargo

    @property
    def balance(self):
        return self._balance

    def credit(self, amount):
        """Add money to the ship's balance."""
        if not isinstance(amount, (int, float)):
            raise TypeError("Amount must be a number")
        if amount < 0:
            raise ValueError("Cannot credit a negative amount")
        self._balance += amount

    def debit(self, amount):
        """Subtract money from the ship's balance."""
        if not isinstance(amount, (int, float)):
            raise TypeError("Amount must be a number")
        if amount < 0:
            raise ValueError("Cannot debit a negative amount")
        if amount > self._balance:
            raise ValueError("Insufficient funds")
        self._balance -= amount
