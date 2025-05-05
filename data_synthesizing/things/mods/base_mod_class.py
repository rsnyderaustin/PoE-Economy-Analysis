from abc import ABC



class Mod(ABC):

    def __init__(self,
                 mod_id: str):
        self.mod_id = mod_id
