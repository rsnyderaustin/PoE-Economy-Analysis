from datetime import datetime
import uuid

import uuid
from datetime import datetime

from src.market_item_analysis.data_handling import utils
from src.market_item_analysis.shared import utils as shared_utils
from src.market_item_analysis.shared.enums.item_enums import EquipmentCategory
from src.market_item_analysis.shared.enums.trade_enums import ModClass, Rarity, Currency


class ItemMod:

    def __init__(self,
                 mod_text: str,
                 mod_class: ModClass):
        self.mod_text = mod_text
        self.mod_class = mod_class

    def to_dict(self) -> dict:
        return shared_utils.generic_to_dict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "ItemMod":
        d['mod_class'] = ModClass(d['mod_class'])
        return cls(**d)


class ItemSkill:

    def __init__(self,
                 name: str,
                 level: int = None):
        self.name = name
        self.level = level or 1

    def to_dict(self) -> dict:
        return shared_utils.generic_to_dict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "ItemSkill":
        return cls(**d)


class ListingMetadata:

    def __init__(self,
                 poster_account_name: str,
                 listing_id: str,
                 date_posted: datetime,
                 date_fetched: datetime):
        self.poster_account_name = poster_account_name
        self.listing_id = listing_id
        self.date_posted = date_posted
        self.date_fetched = date_fetched

    def to_dict(self) -> dict:
        return shared_utils.generic_to_dict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "ListingMetadata":
        d['date_posted'] = datetime.fromisoformat(d['date_posted'])
        d['date_fetched'] = datetime.fromisoformat(d['date_fetched'])
        return cls(**d)


class EquipmentRequirements:

    def __init__(self,
                 player_level: int,
                 strength: int,
                 intelligence: int,
                 dexterity: int):
        self.player_level = player_level
        self.strength = strength
        self.intelligence = intelligence
        self.dexterity = dexterity

    def to_dict(self) -> dict:
        return shared_utils.generic_to_dict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "EquipmentRequirements":
        return cls(**d)


class ItemMods:

    def __init__(self,
                 implicits: list[ItemMod] | None = None,
                 enchants: list[ItemMod] | None = None,
                 fractures: list[ItemMod] | None = None,
                 explicits: list[ItemMod] | None = None):
        self.implicits = implicits or []
        self.enchants = enchants or []
        self.fractures = fractures or []
        self.explicits = explicits or []

        self._mod_class_d = {
            ModClass.IMPLICIT: self.implicits,
            ModClass.ENCHANT: self.enchants,
            ModClass.FRACTURED: self.fractures,
            ModClass.EXPLICIT: self.explicits
        }

    def to_dict(self) -> dict:
        return shared_utils.generic_to_dict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "ItemMods":
        return ItemMods(
            implicits=[ItemMod.from_dict(v) for v in d['implicits']] if 'implicits' in d else None,
            enchants=[ItemMod.from_dict(v) for v in d['enchants']] if 'enchants' in d else None,
            fractures=[ItemMod.from_dict(v) for v in d['fractures']] if 'fractures' in d else None,
            explicits=[ItemMod.from_dict(v) for v in d['explicits']] if 'explicits' in d else None
        )


    @property
    def all_mods(self) -> list[ItemMod]:
        return [m
                for mods_list in self._mod_class_d.values()
                for m in mods_list]

    def add_mod(self, mod: ItemMod):
        mods = self._mod_class_d[mod.mod_class]
        mods.append(mod)

    def fetch_mods(self, mod_class: ModClass) -> list[ItemMod]:
        return self._mod_class_d[mod_class]


class ItemTypes:

    def __init__(self,
                 base_name: str,
                 item_category: EquipmentCategory):
        """

        :param base_name: Ex: Hunting Shoes, Lunar Amulet, etc
        :param item_category: Ex: DEX Body Armour, INT/DEX Gloves, One Handed Mace, etc
        """
        self.base_name = base_name
        self.item_category = item_category

    def to_dict(self) -> dict:
        return shared_utils.generic_to_dict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "ItemTypes":
        return ItemTypes(
            base_name=d['base_name'],
            item_category=EquipmentCategory(d['item_category'])
        )


class Price:

    def __init__(self,
                 currency: Currency,
                 currency_amount: int,
                 gold_cost: int):
        self.currency = currency
        self.currency_amount = currency_amount
        self.gold_cost = gold_cost

    def to_dict(self) -> dict:
        return shared_utils.generic_to_dict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Price":
        return Price(
            currency=Currency(d['currency']),
            currency_amount=int(d['currency_amount']),
            gold_cost=int(d['gold_cost'])
        )


class EquipmentStats:

    def __init__(self,
                 armour: int = None,
                 energy_shield: int = None,
                 evasion: int = None,
                 attacks_per_second: float = None,
                 physical_damage: float = None,
                 critical_hit_chance: float = None,
                 cold_damage: float = None,
                 fire_damage: float = None,
                 lightning_damage: float = None,
                 chaos_damage: float = None):
        self.armour = armour or 0
        self.energy_shield = energy_shield or 0
        self.evasion = evasion or 0
        self.attacks_per_second = attacks_per_second or 0
        self.physical_damage = physical_damage or 0
        self.critical_hit_chance = critical_hit_chance or 0
        self.cold_damage = cold_damage or 0
        self.fire_damage = fire_damage or 0
        self.lightning_damage = lightning_damage or 0
        self.chaos_damage = chaos_damage or 0

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, d: dict) -> "EquipmentStats":
        return cls(**d)


class EquipmentProperties:

    def __init__(self,
                 rarity: Rarity,
                 ilvl: int,
                 identified: bool,
                 corrupted: bool,
                 quality: int,
                 open_prefixes: int,
                 open_suffixes: int,
                 **additional_properties):
        self.rarity = rarity
        self.ilvl = ilvl
        self.identified = identified
        self.corrupted = corrupted
        self.quality = quality
        self.open_suffixes = open_suffixes
        self.open_prefixes = open_prefixes

        self.additional_properties = additional_properties

    def to_dict(self) -> dict:
        return shared_utils.generic_to_dict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "EquipmentProperties":
        d['rarity'] = Rarity(d['rarity'])
        d['identified'] = bool(d['identified'])
        d['corrupted'] = bool(d['corrupted'])

        for k, v in d['additional_properties'].items():
            d[k] = v

        del d['additional_properties']

        return cls(**d)


class EquipmentListing:

    def __init__(self,
                 metadata: ListingMetadata,
                 price: Price,
                 item_name: str,
                 types: ItemTypes,
                 requirements: EquipmentRequirements,
                 stats: EquipmentStats,
                 mods_: ItemMods,
                 skills: list[ItemSkill],
                 properties: EquipmentProperties,
                 internal_id: str = None
                 ):
        self.metadata = metadata
        self.price = price
        self.item_name = item_name
        self.types = types
        self.requirements = requirements
        self.stats = stats
        self.mods_ = mods_
        self.skills = skills
        self.properties = properties

        self.internal_id = internal_id or uuid.uuid4().hex

    def __key(self):
        return self.metadata.listing_id

    def __hash__(self):
        return hash(self.__key())

    def __gt__(self, other):
        if not isinstance(other, EquipmentListing):
            return NotImplemented

        return self.metadata.date_fetched > other.metadata.date_fetched

    def __lt__(self, other):
        if not isinstance(other, EquipmentListing):
            return NotImplemented

        return self.metadata.date_fetched < other.metadata.date_fetched

    def __eq__(self, other):
        if not isinstance(other, EquipmentListing):
            return NotImplemented

        return self.__key() == other.__key()

    def to_dict(self) -> dict:
        return shared_utils.generic_to_dict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "EquipmentListing":
        d['metadata'] = ListingMetadata.from_dict(d['metadata'])
        d['price'] = Price.from_dict(d['price'])
        d['types'] = ItemTypes.from_dict(d['types'])
        d['requirements'] = EquipmentRequirements.from_dict(d['requirements'])
        d['mods'] = ItemMods.from_dict(d['mods'])
        d['skills'] = [ItemSkill.from_dict(s) for s in d['skills']]
        d['properties'] = EquipmentProperties.from_dict(d['properties'])
        return cls(**d)

    @property
    def minutes_since_listed(self):
        return utils.determine_minutes_since(
            relevant_date=self.metadata.date_fetched
        )

    @property
    def minutes_since_league_start(self):
        return utils.determine_minutes_since(
            relevant_date=utils.league_start_date,
            later_date=self.metadata.date_fetched
        )


