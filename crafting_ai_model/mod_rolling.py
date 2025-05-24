import random

from file_management import FilesManager, DataPath
from instances_and_definitions import ModifiableListing, ItemMod
from shared import ModClass
from shared.item_enums import ModAffixType


def _mods_into_dict(mods: list[ItemMod]):
    """

    :param mods:
    :return: A nested dict of mods by their atype and mod class.
    """
    d = dict()
    for mod in mods:
        if mod.atype not in d:
            d[mod.atype] = dict()

        if mod.mod_class_e not in d[mod.atype]:
            d[mod.atype][mod.mod_class_e] = set()

        d[mod.atype][mod.mod_class_e].add(mod)

    return d


class ModsFetcher:

    def __init__(self):
        files_manager = FilesManager()
        mods = files_manager.file_data[DataPath.MODS]

        self.mods_dict = _mods_into_dict(mods)

    def fetch_mod_tiers(self,
                        atype: str,
                        max_ilvl: int,
                        mod_class: ModClass,
                        force_mod_type: str = None,
                        exclude_mod_ids: set[str] = None,
                        affix_types: list[ModAffixType] = None) -> list[ItemMod]:
        mods = self.mods_dict[atype][mod_class]

        mods = [mod for mod in mods if mod.ilvl <= max_ilvl]

        if force_mod_type:
            mods = [mod for mod in mods if force_mod_type in mod.mod_types]

        if exclude_mod_ids:
            mods = [mod for mod in mods if mod.mod_id != exclude_mod_ids]

        if affix_types:
            mods = [mod for mod in mods if mod.affix_type in affix_types]

        return mods


class ModRoller:
    _instance = None
    _initialized = False

    def __new__(cls):
        if not hasattr(cls, '_instance'):
            cls._instance = super(ModRoller, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        cls = self.__class__
        if getattr(cls, '_initialized', False):
            return

        # Need to validate that we have all or nearly all of the mods represented in Poecd
        self.mods_manager = ModsFetcher()

        cls._initialized = True

    def roll_new_modifier(self,
                          listing: ModifiableListing,
                          mod_class: ModClass,
                          force_type: str = None,
                          exclude_mod_ids: set = None,
                          force_affix_type: ModAffixType = None) -> ItemMod:
        """

        :param force_affix_type:
        :param mod_class:
        :param listing:
        :param force_type:
        :param exclude_mod_ids: If not supplied, the function assumes that all current mods on the item are not eligible to roll.
        :return: All the possible crafting outcomes given the function's parameters
        """

        if force_affix_type:
            affix_types = [force_affix_type]
        else:
            affix_types = []
            if listing.open_prefixes:
                affix_types.append(ModAffixType.PREFIX)

            if listing.open_suffixes:
                affix_types.append(ModAffixType.SUFFIX)

        atype_item_mods = self.mods_manager.fetch_mod_tiers(
            atype=listing.item_atype,
            max_ilvl=listing.ilvl,
            mod_class=mod_class,
            force_mod_type=force_type,
            exclude_mod_ids=set(mod.mod_id for mod in listing.mods) if not exclude_mod_ids else exclude_mod_ids,
            affix_types=affix_types
        )

        total_weight = sum(item_mod.weighting for item_mod in atype_item_mods)

        new_mod = random.choices(atype_item_mods,
                                 weights=[(mod.weighting / total_weight) for mod in atype_item_mods],
                                 k=1)[0]

        return new_mod


