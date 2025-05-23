from shared import ItemCategory


local_weapon_mod_cols = [
    'Attacks per Second',
    'Physical Damage',
    'Cold Damage',
    'Fire Damage',
    'Lightning Damage',
    'adds_#_to_#_fire_damage',
    '#%_increased_attack_speed',
    '#%_increased_physical_damage',
    'adds_#_to_#_cold_damage',
    'adds_#_to_#_lightning_damage',
    'adds_#_to_#_physical_damage',
    '+#.#%_to_critical_hit_chance',
    '+#%_to_critical_hit_chance',
    '#% increased Physical Damage',
    'Adds # to # Fire Damage',
    'Adds # to # Lightning Damage',
    'Adds # to # Cold Damage',
    '#% increased Attack Speed',
    'Quality'
]


socketable_item_categories = [
    ItemCategory.ONE_HANDED_MACE,
    ItemCategory.SPEAR,
    ItemCategory.TWO_HANDED_MACE,
    ItemCategory.QUARTERSTAFF,
    ItemCategory.BOW,
    ItemCategory.CROSSBOW,
    ItemCategory.WAND,
    ItemCategory.SCEPTRE,
    ItemCategory.STAFF,
    ItemCategory.HELMET,
    ItemCategory.BODY_ARMOUR,
    ItemCategory.GLOVES,
    ItemCategory.BOOTS,
    ItemCategory.SHIELD,
    ItemCategory.FOCUS,
    ItemCategory.BUCKLER
]

martial_weapon_categories = [
    ItemCategory.ONE_HANDED_MACE,
    ItemCategory.SPEAR,
    ItemCategory.TWO_HANDED_MACE,
    ItemCategory.QUARTERSTAFF,
    ItemCategory.BOW,
    ItemCategory.CROSSBOW
]

non_martial_weapon_categories = [
    ItemCategory.WAND,
    ItemCategory.SCEPTRE,
    ItemCategory.STAFF
]

armour_categories = [
    ItemCategory.HELMET,
    ItemCategory.BODY_ARMOUR,
    ItemCategory.GLOVES,
    ItemCategory.BOOTS,
    ItemCategory.QUIVER,
    ItemCategory.SHIELD,
    ItemCategory.FOCUS,
    ItemCategory.BUCKLER
]


flask_categories = [
    ItemCategory.LIFE_FLASK,
    ItemCategory.MANA_FLASK
]
