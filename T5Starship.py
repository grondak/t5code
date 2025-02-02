import T5Mail
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
        self.mail = {}
        self.mailLockerSize = 5
        self.destinationWorld = None
        
    def set_course_for(self, destination):
        self.destinationWorld = destination
    
    def destination(self):
        return self.destinationWorld
    
    def onload_high_passenger(self, npc):
        if npc in self.highPassengers:
            errorResult = 'Cannot load same passenger ' + npc.characterName + ' twice.'
            raise DuplicateItemError(errorResult)
        self.highPassengers.add(npc)
        npc.location = self.shipName
        
    def offload_high_passengers(self):
        offloadedPassengers = set()
        for npc in list(self.highPassengers):
            npc.location = self.location
            self.highPassengers.remove(npc)
            offloadedPassengers.add(npc)
        return offloadedPassengers
    
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