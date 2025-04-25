
from items import Armour, Flask, Jewellery

class ObjectTypeToClass:

    _object_type_to_class = {
        'Flask': Flask,
        'Amulet': Jewellery,
        'Ring': Jewellery,
        'Belt': Armour
    }

    @classmethod