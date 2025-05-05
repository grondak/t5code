import T5Mail
from T5NPC import T5NPC
from T5Basics import check_success
import uuid

class DuplicateItemError(Exception):
    """Custom exception for duplicate set items."""
    pass

class T5Starship:
    """A starship class intended to implement just enough of the T5 Starship concepts to function in the simulator"""
    
    def __init__(self, ship_name, ship_location):
        self.shipName = ship_name
        self.location = ship_location
        self.highPassengers = set()
        self.passengers = dict([('high', set()), ('mid', set()), ('low', set()), ('all', set())])
        self.mail = {}
        self.crew = {}
        self.mailLockerSize = 5
        self.destinationWorld = None
        
    def set_course_for(self, destination):
        self.destinationWorld = destination
    
    def destination(self):
        return self.destinationWorld
    
    def onload_passenger(self, npc, passageClass):
        if not(isinstance(npc, T5NPC)):
            raise TypeError('Invalid passenger type.')
        ALLOWED_PASSAGE_CLASSES = ['high', 'mid', 'low']
        if passageClass not in ALLOWED_PASSAGE_CLASSES:
            raise ValueError('Invalid passenger class.')
        if npc in self.passengers['all']:
            errorResult = 'Cannot load same passenger ' + npc.characterName + ' twice.'
            raise DuplicateItemError(errorResult)
        self.passengers['all'].add(npc)
        self.passengers[passageClass].add(npc)
        npc.location = self.shipName
                
    def offload_passengers(self, passageClass):
        offloadedPassengers = set()
        ALLOWED_PASSAGE_CLASSES = ['high', 'mid', 'low']
        if passageClass not in ALLOWED_PASSAGE_CLASSES:
            raise ValueError('Invalid passenger class.')
        for npc in list(self.passengers[passageClass]):
            if passageClass == 'low':
                self.awakenLowPassenger(npc, self.crew.get('medic'))
            npc.location = self.location
            self.passengers[passageClass].remove(npc)
            self.passengers['all'].remove(npc)
            offloadedPassengers.add(npc)
        return offloadedPassengers
    
    def awakenLowPassenger(self, npc, medic, roll_override_in: int = None):
        if check_success(roll_override = roll_override_in, skills_override = medic.skills):
            return True
        else:
            npc.kill()
            return False
    
    def onload_mail(self, mailItem):
        if len(self.mail.keys()) > self.mailLockerSize:
            raise ValueError('Starship mail locker size exceeded.')
        self.mail[mailItem.serial] = mailItem
       
    def offload_mail(self):
        if (len(self.mail.keys()) == 0):
            raise ValueError('Starship has no mail to offload.')
        self.mail = {}
    
    def get_mail(self):
        return self.mail
    
    def hire_crew(self, position, npc):
        ALLOWED_CREW_POSITIONS = ['medic']
        if position not in ALLOWED_CREW_POSITIONS:
            raise ValueError('Invalid crew position.')
        if not(isinstance(npc, T5NPC)):
            raise TypeError('Invalid NPC.')     
        self.crew[position] = npc