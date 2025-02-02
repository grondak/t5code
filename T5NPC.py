import uuid

class T5NPC:
    """An NPC class intended to implement just enough of the T5 character concepts to function in the simulator"""
    
    def __init__(self, character_name):
        self.characterName = character_name
        self.serial = str(uuid.uuid4())
        self.location = None
        
    def update_location(self, location):
        self.location = location