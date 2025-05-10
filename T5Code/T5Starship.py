import T5Code.T5Mail
from T5Code.T5NPC import T5NPC
from T5Code.T5Basics import check_success
from T5Code.T5ShipClass import T5ShipClass
from T5Code.T5Lot import T5Lot
import uuid


class DuplicateItemError(Exception):
    """Custom exception for duplicate set items."""

    pass


class T5Starship:
    """A starship class intended to implement just enough of the T5 Starship concepts to function in the simulator"""

    def __init__(self, ship_name, ship_location, ship_class: T5ShipClass):
        self.shipName = ship_name
        self.location = ship_location
        self.holdSize = ship_class.cargoCapacity
        self.highPassengers = set()
        self.passengers = dict(
            [("high", set()), ("mid", set()), ("low", set()), ("all", set())]
        )
        self.mail = {}
        self.crew = {}
        self.cargo = {"freight": [], "cargo": []}
        self.cargoSize = 0
        self.mailLockerSize = 5
        self.destinationWorld = None

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
        if len(self.mail.keys()) > self.mailLockerSize:
            raise ValueError("Starship mail locker size exceeded.")
        self.mail[mailItem.serial] = mailItem

    def offload_mail(self):
        if len(self.mail.keys()) == 0:
            raise ValueError("Starship has no mail to offload.")
        self.mail = {}

    def get_mail(self):
        return self.mail

    def hire_crew(self, position, npc: T5NPC):
        ALLOWED_CREW_POSITIONS = ["medic"]
        if position not in ALLOWED_CREW_POSITIONS:
            raise ValueError("Invalid crew position.")
        if not (isinstance(npc, T5NPC)):
            raise TypeError("Invalid NPC.")
        self.crew[position] = npc

    def onload_lot(self, inLot: T5Lot, lotType):
        if not (isinstance(inLot, T5Lot)):
            raise TypeError("Invalid lot type.")
        if not ((lotType == "cargo") or (lotType == "freight")):
            raise ValueError("Invalid lot value.")
        if inLot.mass + self.cargoSize > self.holdSize:
            raise ValueError("Lot will not fit in remaining space.")
        if (inLot in self.cargo["freight"]) or (inLot in self.cargo["cargo"]):
            raise ValueError("Attempt to load same lot twice.")
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
