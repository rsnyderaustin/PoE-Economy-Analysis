
from items import Armour, Flask, Jewellery, Weapon

class ObjectTypeToClass:

    _object_type_to_class = {
        'Flask': Flask,
        'Amulet': Jewellery,
        'Ring': Jewellery,
        'Belt': Armour,
        'Spear': Weapon,
        'One Hand Sword': Weapon,
        'One Hand Axe': Weapon,
        'One Hand Mace': Weapon,
        'Two Hand Sword': Weapon,
        'Two Hand Axe': Weapon
        'Two Hand Mace': Weapon,
    }

    @classmethod