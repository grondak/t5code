import uuid

class T5NPC:
    """An NPC class intended to implement just enough of the T5 character concepts to function in the simulator"""
    
    def __init__(self, character_name):
        self.characterName = character_name
        self.serial = str(uuid.uuid4())
        self.location = None
        self.skills = {}
        self.state = 'Alive'
        
    def update_location(self, location):
        self.location = location
        
    def set_skill(self, skill, value):
        self.skills[skill]= value
        
    def get_skill(self, skill):
        return self.skills.get(skill, 0)
    
    def kill(self):
        self.state = 'Dead'
        
    def get_state(self):
        return self.state
        
    