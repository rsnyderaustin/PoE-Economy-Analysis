from abc import ABC, abstractmethod

import numpy as np

import uuid
from datetime import datetime

from src.market_item_analysis.core import utils as shared_utils
from src.market_item_analysis.shared.enums.item_enums import EquipmentCategory, AffixType
from src.market_item_analysis.shared.enums.trade_enums import ModClass, Rarity, Currency

from src.market_item_analysis.core.dictionary_service import DictionaryService
from src.market_item_analysis.core.string_service import TextAnalyzer
from src.market_item_analysis.trade_api.trade_result import ApiResponse


class TradeApiResponseObject(ABC):

    def to_dict(self) -> dict:
        return DictionaryService.convert_to_dict(self)

    @classmethod
    @abstractmethod
    def from_dict(cls, d: dict):
        pass


class ItemMod(TradeApiResponseObject):

    def __init__(self,
                 mod_text: str,
                 mod_class: ModClass,
                 affix_type: AffixType | None = None):
        self.mod_text = mod_text
        self.mod_class = mod_class

        self.affix_type = affix_type

    @classmethod
    def from_dict(cls, d: dict) -> "ItemMod":
        d['mod_class'] = ModClass(d['mod_class'])
        d['affix_type'] = AffixType(d['affix_type']) if 'affix_type' in d else None
        return cls(**d)


class EquipmentSkill(TradeApiResponseObject):

    def __init__(self,
                 name: str,
                 level: int = None):
        self.name = name
        self.level = level or 1

    @classmethod
    def from_dict(cls, d: dict) -> "EquipmentSkill":
        return cls(**d)


class ListingMetadata(TradeApiResponseObject):

    def __init__(self,
                 poster_account_name: str,
                 listing_id: str,
                 date_posted: datetime,
                 date_fetched: datetime):
        self.poster_account_name = poster_account_name
        self.listing_id = listing_id
        self.date_posted = date_posted
        self.date_fetched = date_fetched

    @classmethod
    def from_dict(cls, d: dict) -> "ListingMetadata":
        d['date_posted'] = datetime.fromisoformat(d['date_posted'])
        d['date_fetched'] = datetime.fromisoformat(d['date_fetched'])
        return cls(**d)

    @classmethod
    def from_api_response(cls, r: TradeApiResponse) -> "ListingMetadata":
        return ListingMetadata(
            poster_account_name=r.account_name,
            listing_id=r.listing_id,
            date_posted=r.date_fetched,
            date_fetched=datetime.now()
        )


class EquipmentRequirements(TradeApiResponseObject):

    def __init__(self,
                 player_level: int,
                 strength: int,
                 intelligence: int,
                 dexterity: int):
        self.player_level = player_level
        self.strength = strength
        self.intelligence = intelligence
        self.dexterity = dexterity

    @classmethod
    def from_dict(cls, d: dict) -> "EquipmentRequirements":
        return cls(**d)

    @classmethod
    def from_api_response(cls, r: ApiResponse) -> "EquipmentRequirements":
        return EquipmentRequirements(
            player_level=r.level_requirement,
            strength=r.strength_requirement,
            intelligence=r.intelligence_requirement,
            dexterity=r.dexterity_requirement
        )


class EquipmentSkills(TradeApiResponseObject):

    def __init__(self,
                 skills: list[EquipmentSkill]):
        self.skills = skills

    @classmethod
    def from_dict(cls, d: dict) -> "EquipmentSkills":
        return cls([EquipmentSkill.from_dict(skill_d) for skill_d in d['skills']])

    @classmethod
    def from_api_response(cls, r: ApiResponse) -> "EquipmentSkills":
        if not r.skills_data:
            return EquipmentSkills(skills=[])

        skills = []
        for skill_data in r.skills_data:
            raw_skill = skill_data['values'][0]

            # Spear Throw is the only skill that is granted by an item without a level. May have to update in the future
            if raw_skill[0] == 'Spear Throw':
                new_skill = EquipmentSkill(
                    name='Spear Throw'
                )
                skills.append(new_skill)
                continue

            if isinstance(raw_skill, str):
                _, level_str, *skill_parts = raw_skill.split()
                level = int(level_str)
                skill_name = ' '.join(skill_parts)
            else:
                skill_name = raw_skill[0][0]
                level = raw_skill[0][1]

            new_skill = EquipmentSkill(
                name=skill_name,
                level=level
            )

            skills.append(new_skill)

        return EquipmentSkills(skills=skills)

class ItemMods(TradeApiResponseObject):

    def __init__(self,
                 mods_d: dict[ModClass, list[ItemMod]]):
        self._mods_d = mods_d

    @property
    def implicits(self):
        return self._mods_d.get(ModClass.IMPLICIT, [])

    @property
    def explicits(self):
        return self._mods_d.get(ModClass.EXPLICIT, [])

    @property
    def enchants(self):
        return self._mods_d.get(ModClass.ENCHANT, [])

    @property
    def fractures(self):
        return self._mods_d.get(ModClass.FRACTURED, [])

    @property
    def runes(self):
        return self._mods_d.get(ModClass.RUNE, [])

    @classmethod
    def from_dict(cls, d: dict) -> "ItemMods":
        mods_d = {}
        for mod_class_str, mod_dicts in d.items():
            mod_class = ModClass(mod_class_str)
            mods = [ItemMod.from_dict(d) for d in mod_dicts]

            mods_d[mod_class] = mods

        return ItemMods(mods_d=mods_d)

    @classmethod
    def from_api_response(cls, r: ApiResponse) -> "ItemMods":

        mods_d = {
            ModClass.IMPLICIT: [],
            ModClass.ENCHANT: [],
            ModClass.FRACTURED: [],
            ModClass.EXPLICIT: [],
            ModClass.RUNE: []
        }
        for mod_class in ModClass:
            if mod_class.api_key not in r.item_data:
                continue

            mod_dicts = r.item_data[mod_class.api_key]
            new_mods = [ItemMod(mod_text=mod_text,
                                mod_class=mod_class) for mod_text in mod_dicts]

            mods_d[mod_class].extend(new_mods)

        item_mods = ItemMods(mods_d=mods_d)
        return item_mods

    @property
    def all_mods(self) -> list[ItemMod]:
        return [m
                for mods_list in self._mods_d.values()
                for m in mods_list]

    def add_mod(self, mod: ItemMod):
        self._mods_d[mod.mod_class].append(mod)

    def fetch_mods_by_class(self, mod_class: ModClass) -> list[ItemMod]:
        return self._mods_d[mod_class]


class ItemTypes(TradeApiResponseObject):

    def __init__(self,
                 base_name: str,
                 item_category: EquipmentCategory):
        """

        :param base_name: Ex: Hunting Shoes, Lunar Amulet, etc
        :param item_category: Ex: DEX Body Armour, INT/DEX Gloves, One Handed Mace, etc
        """
        self.base_name = base_name
        self.item_category = item_category

    @classmethod
    def from_dict(cls, d: dict) -> "ItemTypes":
        return ItemTypes(
            base_name=d['base_name'],
            item_category=EquipmentCategory(d['item_category'])
        )


class EquipmentNamespace(TradeApiResponseObject):

    def __init__(self,
                 base_name: str):
        self.base_name = base_name

    @classmethod
    def from_dict(cls, d: dict) -> "EquipmentNamespace":
        return EquipmentNamespace(base_name=d['base_name'])

    @classmethod
    def from_api_response(cls, r: TradeApiResponse) -> "EquipmentNamespace":
        return EquipmentNamespace(base_name=r.base_name)


class EquipmentPrice(TradeApiResponseObject):

    def __init__(self,
                 currency: Currency,
                 currency_amount: int,
                 gold_cost: int):
        self.currency = currency
        self.currency_amount = currency_amount
        self.gold_cost = gold_cost

    @classmethod
    def from_dict(cls, d: dict) -> "EquipmentPrice":
        return EquipmentPrice(
            currency=Currency(d['currency']),
            currency_amount=int(d['currency_amount']),
            gold_cost=int(d['gold_cost'])
        )

    @classmethod
    def from_api_response(cls, r: ApiResponse) -> "EquipmentPrice":
        return EquipmentPrice(
            currency=Currency(r.price_currency),
            currency_amount=r.price_amount,
            gold_cost=r.gold_cost
        )


class EquipmentStats(TradeApiResponseObject):

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

    @classmethod
    def from_dict(cls, d: dict) -> "EquipmentStats":
        return cls(**d)

    @classmethod
    def _pull_value(cls, stat: str, r: ApiResponse) -> float | int | None:
        properties_list = r.item_data['properties']
        stat_dicts = [d for d in properties_list if d['name'] == stat]
        if not stat_dicts:
            return None

        if len(stat_dicts) >= 2:
            raise ValueError(f"Found 2 stats dicts for {stat}.\nSource data: {properties_list}")

        val_str = stat_dicts[0]['values'][0]
        vals = TextAnalyzer.extract_numbers_from_string(val_str)
        return np.mean(vals)

    @classmethod
    def from_api_response(cls, r: ApiResponse) -> "EquipmentStats":
        armour = cls._pull_value(stat='[Armour]', r=r)
        evasion = cls._pull_value(stat='[Evasion|Evasion Rating]', r=r)
        energy_shield = cls._pull_value(stat='[Energy Shield|Energy Shield]', r=r)

        elemental_damage = r.determine_elemental_damage_values()

        phys_damage = cls._pull_value(stat='[Physical] Damage', r=r)
        crit_chance = cls._pull_value(stat='[Critical|Critical Hit] Chance', r=r)
        attacks_per_second = cls._pull_value(stat='Attacks per Second', r=r)

        return EquipmentStats(
            armour=armour,
            evasion=evasion,
            energy_shield=energy_shield,
            fire_damage=elemental_damage.fire,
            cold_damage=elemental_damage.cold,
            lightning_damage=elemental_damage.lightning,
            physical_damage=phys_damage,
            critical_hit_chance=crit_chance,
            attacks_per_second=attacks_per_second
        )



class EquipmentProperties(TradeApiResponseObject):

    def __init__(self,
                 rarity: Rarity,
                 ilvl: int,
                 identified: bool,
                 corrupted: bool,
                 quality: int,
                 **additional_properties):
        self.rarity = rarity
        self.ilvl = ilvl
        self.identified = identified
        self.corrupted = corrupted
        self.quality = quality

        self.additional_properties = additional_properties

    @classmethod
    def from_dict(cls, d: dict) -> "EquipmentProperties":
        d['rarity'] = Rarity(d['rarity'])
        d['identified'] = bool(d['identified'])
        d['corrupted'] = bool(d['corrupted'])

        for k, v in d['additional_properties'].items():
            d[k] = v

        del d['additional_properties']

        return cls(**d)


class EquipmentListing(TradeApiResponseObject):

    def __init__(self,
                 metadata: ListingMetadata,
                 price: EquipmentPrice,
                 namespace: EquipmentNamespace,
                 types: ItemTypes,
                 requirements: EquipmentRequirements,
                 stats: EquipmentStats,
                 mods_: ItemMods,
                 skills: list[EquipmentSkill],
                 properties: EquipmentProperties,
                 internal_id: str = None
                 ):
        self.metadata = metadata
        self.price = price
        self.namespace = namespace
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

    @classmethod
    def from_dict(cls, d: dict) -> "EquipmentListing":
        d['metadata'] = ListingMetadata.from_dict(d['metadata'])
        d['price'] = EquipmentPrice.from_dict(d['price'])
        d['namespace'] = EquipmentNamespace.from_dict(d['namespace'])
        d['types'] = ItemTypes.from_dict(d['types'])
        d['requirements'] = EquipmentRequirements.from_dict(d['requirements'])
        d['mods'] = ItemMods.from_dict(d['mods'])
        d['skills'] = [EquipmentSkill.from_dict(s) for s in d['skills']]
        d['properties'] = EquipmentProperties.from_dict(d['properties'])
        return cls(**d)

    @classmethod
    def from_api_response(cls, r: ApiResponse) -> "EquipmentListing":
        return cls(
            metadata=ListingMetadata.from_api_response(r),
            price=EquipmentPrice.from_api_response(r),
            namespace=EquipmentNamespace.from_api_response(r),
            types=ItemTypes.from_api_response(r),
            requirements=EquipmentRequirements.from_api_response(r),
            stats=ItemStats.from_api_response(r),
            mods_=ItemMods.from_api_response(r),
            skills=EquipmentSkill.from_api_response(r),
            properties=EquipmentProperties.from_api_response(r),
        )

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


