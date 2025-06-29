import uuid

import t5code.T5Mail
from t5code.T5Basics import check_success
from t5code.T5Lot import T5Lot
from t5code.T5NPC import T5NPC
from t5code.T5ShipClass import T5ShipClass


class DuplicateItemError(Exception):
    """Custom exception for duplicate set items."""

    pass


class _BestCrewSkillDict:
    def __init__(self, crew_dict):
        self.crew = crew_dict

    def __getitem__(self, skill_name):
        skill_name = skill_name.lower()
        return max(
            (member.get_skill(skill_name) for member in self.crew.values()), default=0
        )


class T5Starship:
    """A starship class intended to implement just enough of the T5 Starship concepts to function in the simulator"""

    def __init__(self, ship_name, ship_location, ship_class: T5ShipClass):
        # Core identity
        self.shipName = ship_name
        self.location = ship_location
        self.holdSize = ship_class.cargoCapacity

        # Passenger system
        self.highPassengers = set()
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
        self.cargoSize = 0  # total tons of cargo on board
        self.mailLockerSize = 1  # max number of mail containers

        # Navigation
        self.destinationWorld = None  # assigned when a flight plan is set

        # Financials
        self._balance = 0.0  # in credits (millions, thousands — your scale)

    def set_course_for(self, destination):
        self.destinationWorld = destination

    def destination(self):
        return self.destinationWorld

    def onload_passenger(self, npc, passageClass):
        if not (isinstance(npc, T5NPC)):
            raise TypeError("Invalid passenger type.")
        ALLOWED_PASSAGE_CLASSES = ["high", "mid", "low"]
        if passageClass not in ALLOWED_PASSAGE_CLASSES:
            raise ValueError("Invalid passenger class.")
        if npc in self.passengers["all"]:
            errorResult = "Cannot load same passenger " + npc.characterName + " twice."
            raise DuplicateItemError(errorResult)
        self.passengers["all"].add(npc)
        self.passengers[passageClass].add(npc)
        npc.location = self.shipName

    def offload_passengers(self, passageClass):
        offloadedPassengers = set()
        ALLOWED_PASSAGE_CLASSES = ["high", "mid", "low"]
        if passageClass not in ALLOWED_PASSAGE_CLASSES:
            raise ValueError("Invalid passenger class.")
        for npc in list(self.passengers[passageClass]):
            if passageClass == "low":
                self.awakenLowPassenger(npc, self.crew.get("medic"))
            npc.location = self.location
            self.passengers[passageClass].remove(npc)
            self.passengers["all"].remove(npc)
            offloadedPassengers.add(npc)
        return offloadedPassengers

    def awakenLowPassenger(self, npc: T5NPC, medic, roll_override_in: int = None):
        if check_success(roll_override=roll_override_in, skills_override=medic.skills):
            return True
        else:
            npc.kill()
            return False

    def onload_mail(self, mailItem):
        if len(self.mail.keys()) >= self.mailLockerSize:
            raise ValueError("Starship mail locker size exceeded.")
        self.mail[mailItem.serial] = mailItem

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
    def bestCrewSkill(self):
        return _BestCrewSkillDict(self.crew)

    ALLOWED_LOT_TYPES = {"cargo", "freight"}

    def can_onload_lot(self, inLot, lotType):
        if not isinstance(inLot, T5Lot):
            raise TypeError("Invalid lot type.")

        if lotType not in self.ALLOWED_LOT_TYPES:
            raise ValueError("Invalid lot value.")

        if inLot.mass + self.cargoSize > self.holdSize:
            raise ValueError("Lot will not fit in remaining space.")

        if inLot in self.cargo["freight"] or inLot in self.cargo["cargo"]:
            raise ValueError("Attempt to load same lot twice.")

        return True  # explicitly returns True if all checks pass

    def onload_lot(self, inLot, lotType):
        if self.can_onload_lot(inLot, lotType):
            self.cargo[lotType].append(inLot)
            self.cargoSize += inLot.mass

    def offload_lot(self, inSerial: uuid, lotType):
        try:
            uuid.UUID(inSerial)
        except ValueError:
            raise ValueError("Invalid lot serial number.")
        if not ((lotType == "cargo") or (lotType == "freight")):
            raise ValueError("Invalid lot value.")
        result = next((l for l in self.cargo[lotType] if l.serial == inSerial), None)

        if result is None:
            raise ValueError("Lot not found as specified type.")
        else:
            self.cargo[lotType].remove(result)
            self.cargoSize -= result.mass
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
