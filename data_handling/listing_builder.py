import copy
import pprint
import re
from dataclasses import dataclass

from file_management.file_managers import ItemModsFile, Poe2DbModsManagerFile
from instances_and_definitions import ItemMod, SubMod, ItemSkill, ModifiableListing, generate_mod_id
from program_logging import LogFile, LogsHandler, log_errors
from shared import shared_utils
from shared.enums.item_enums import ModAffixType, AType
from shared.enums.trade_enums import ModClass
from . import utils
from .api_response_parser import ApiResponseParser
from .mod_matching import ModMatcher

parse_log = LogsHandler().fetch_log(LogFile.API_PARSING)


class ListingBuilder:

    def __init__(self):
        self._mod_resolver = self._create_mod_resolver()

    @staticmethod
    def _create_mod_resolver() -> '_ModResolver':
        item_mods_file = ItemModsFile()

        poe2db_mods_manager = Poe2DbModsManagerFile().load(missing_ok=False)
        mod_matcher = ModMatcher(poe2db_mods_manager)

        poe2db_injector = _PoE2DbInjector(mod_matcher=mod_matcher)  # <-- Typo fix here
        return _ModResolver(item_mods_file=item_mods_file,
                            poe2db_injector=poe2db_injector)

    @staticmethod
    def _build_listing_string(rp: ApiResponseParser):
        if rp.item_properties:
            properties_ = {
                shared_utils.extract_from_brackets(p['name']): shared_utils.extract_values_from_text(p['values'][0][0])[0]
                for p in rp.item_properties[1:]
            }
        else:
            properties_ = {}

        att_requirements = {
            k: v for k, v in {
                'Str': rp.str_requirement,
                'Dex': rp.dex_requirement,
                'Int': rp.int_requirement
            }.items() if v
        }

        implicits = rp.fetch_tiered_mod_strings(mod_class=ModClass.IMPLICIT,
                                                mod_abbrev=ApiResponseParser.mod_class_to_abbrev[ModClass.IMPLICIT])
        enchants = rp.fetch_tiered_mod_strings(mod_class=ModClass.ENCHANT,
                                               mod_abbrev=ApiResponseParser.mod_class_to_abbrev[ModClass.ENCHANT])
        fractureds = rp.fetch_tiered_mod_strings(mod_class=ModClass.FRACTURED,
                                                 mod_abbrev=ApiResponseParser.mod_class_to_abbrev[ModClass.FRACTURED])
        explicits = rp.fetch_tiered_mod_strings(mod_class=ModClass.EXPLICIT,
                                                mod_abbrev=ApiResponseParser.mod_class_to_abbrev[ModClass.EXPLICIT])

        s = []

        s.append(f"{rp.item_name} {rp.item_btype}\n"
                 f"{rp.item_category}\n")

        if properties_:
            s.append('\n'.join(f"{k}: {v}" for k, v in properties_.items()))

        s.append(f"\nItem Level: {rp.item_ilvl}")

        if rp.level_requirement:
            s.append(f"\nRequires Level: {rp.level_requirement} ")
        if att_requirements:
            s.append(', '.join(f"{k}: {v}" for k, v in att_requirements.items()))

        skills = _SkillsFactory.create_skills(rp)
        if skills:
            s.append('\n'.join([f"Grants Skill: Level {skill.level} {skill.name}" for skill in skills]))

        s.append('\n\n' + '\n'.join(implicits + enchants + fractureds + explicits))
        s.append(f"\n\n{rp.price.amount}x {rp.price.currency.value}  IGN: {rp.account_name}")

        return ''.join(s)

    def build_listing(self, rp: ApiResponseParser):
        minutes_since_listed = utils.determine_minutes_since(
            relevant_date=rp.date_fetched
        )
        minutes_since_league_start = utils.determine_minutes_since(
            relevant_date=utils.league_start_date,
            later_date=rp.date_fetched
        )
        item_mods = self._mod_resolver.resolve_mods(rp)

        listing = ModifiableListing(
            listing_str=self._build_listing_string(rp),
            account_name=rp.account_name,
            listing_id=rp.listing_id,
            date_fetched=rp.date_fetched,
            minutes_since_listed=minutes_since_listed,
            minutes_since_league_start=minutes_since_league_start,
            currency=rp.price.currency,
            currency_amount=rp.price.amount,
            item_name=rp.item_name,
            item_btype=rp.item_btype,
            item_atype=rp.item_atype,
            rarity=rp.item_rarity,
            ilvl=rp.item_ilvl,
            identified=rp.is_identified,
            corrupted=rp.is_corrupted,
            implicit_mods=[mod for mod in item_mods if mod.mod_class == ModClass.IMPLICIT],
            enchant_mods=[mod for mod in item_mods if mod.mod_class == ModClass.ENCHANT],
            fractured_mods=[mod for mod in item_mods if mod.mod_class == ModClass.FRACTURED],
            explicit_mods=[mod for mod in item_mods if mod.mod_class == ModClass.EXPLICIT],
            item_skills=_SkillsFactory.create_skills(rp),
            item_properties=rp.item_properties
        )

        return listing


class _ModValueRangesParser:

    @staticmethod
    def determine_sub_mod_value_ranges(mod_magnitudes: list) -> dict:
        """
        {
            X: (10, 15),
            X: (20, 25)
        }
        ---->
        {
            X: [(10, 15), (20, 25)]
        """
        mod_ids = {magnitude['hash'] for magnitude in mod_magnitudes}

        v_ranges = dict()
        for mod_id in mod_ids:
            magnitudes = [magnitude for magnitude in mod_magnitudes if magnitude['hash'] == mod_id]

            value_ranges = [
                (
                    utils.convert_string_into_number(m['min']) if 'min' in m else None,
                    utils.convert_string_into_number(m['max']) if 'max' in m else None
                )
                for m in magnitudes
            ]

            v_ranges[mod_id] = value_ranges

        return v_ranges


class _SubModValuesInjector:

    @staticmethod
    def inject_sub_mod_values(sub_mod_hash_to_text: dict, current_mod: ItemMod):
        sub_mod_hash_to_sub_mod = {sub_mod.sub_mod_hash: sub_mod for sub_mod in current_mod.sub_mods}
        for sub_mod_hash, sub_mod in sub_mod_hash_to_sub_mod.items():
            sub_mod_text = sub_mod_hash_to_text[sub_mod_hash]
            values = shared_utils.extract_values_from_text(sub_mod_text)
            parse_log.info(f"Parsed sub-mod text '{sub_mod_text}' into values {values}")
            sub_mod.actual_values = values


class _PoE2DbInjector:

    def __init__(self, mod_matcher: ModMatcher):
        self.mod_matcher = mod_matcher

    def inject_poe2db_into_mod(self, mod: ItemMod) -> ItemMod:
        # Only explicit mods and fractured mods require weighting and mod types
        if mod.mod_class not in (ModClass.EXPLICIT, ModClass.FRACTURED):
            return mod

        poe2db_mod = self.mod_matcher.match_mod(mod)

        if not poe2db_mod:
            parse_log.error(f"Was not able to match item mod:\n{pprint.pformat(mod)}")
            return mod

        mod.weighting = poe2db_mod.fetch_weighting(ilvl=mod.mod_ilvl)
        mod.mod_types = poe2db_mod.mod_types

        return mod


@dataclass
class _ModMeta:
    mod_atype: AType
    mod_class: ModClass
    sub_mod_hashes: set
    affix_type: ModAffixType | None
    mod_tier: int | None

    @property
    def mod_id(self):
        return generate_mod_id(mod_class=self.mod_class,
                               atype=self.mod_atype,
                               sub_mod_hashes=self.sub_mod_hashes,
                               mod_tier=self.mod_tier,
                               affix_type=self.affix_type)


class _ModFactory:

    @staticmethod
    def _determine_mod_affix_type(mod_data: dict) -> ModAffixType | None:
        mod_affix = None
        if mod_data['tier']:
            first_letter = mod_data['tier'][0]
            if first_letter == 's':
                mod_affix = ModAffixType.SUFFIX
            elif first_letter == 'p':
                mod_affix = ModAffixType.PREFIX
            else:
                parse_log.error(f"Did not recognize first character as an affix type for mod tier {mod_data['tier']}.")
                return None

        return mod_affix

    @staticmethod
    def _determine_mod_tier(mod_data: dict) -> int | None:
        mod_tier = None
        if mod_data['tier']:
            mod_tier_match = re.search(r'\d+', mod_data['tier'])
            if mod_tier_match:
                mod_tier = mod_tier_match.group()
            else:
                parse_log.info(f"Did not find a tier number for mod tier {mod_data['tier']}")
                return None

        return int(mod_tier) if mod_tier else None

    @staticmethod
    def _create_sub_mods(sub_mod_hash_to_text: dict,
                         mod_magnitudes: list) -> list[SubMod]:
        sub_mod_hashes = set(magnitude['hash'] for magnitude in mod_magnitudes)

        mod_id_to_values_ranges = _ModValueRangesParser.determine_sub_mod_value_ranges(mod_magnitudes=mod_magnitudes)

        sub_mods = []
        for sub_mod_hash in sub_mod_hashes:
            sanitized_text = shared_utils.sanitize_mod_text(sub_mod_hash_to_text[sub_mod_hash])

            value_ranges = mod_id_to_values_ranges[sub_mod_hash]

            new_sub_mod = SubMod(
                sub_mod_hash=sub_mod_hash,
                sanitized_text=sanitized_text,
                actual_values=None,
                values_ranges=value_ranges
            )
            sub_mods.append(new_sub_mod)

        return sub_mods

    @classmethod
    def create_mod_meta(cls,
                        mod_class: ModClass,
                        mod_atype: AType,
                        mod_data: dict) -> _ModMeta:
        sub_mod_hashes = set(magnitude['hash'] for magnitude in mod_data['magnitudes'])
        affix_type = cls._determine_mod_affix_type(mod_data)
        mod_tier = cls._determine_mod_tier(mod_data)

        return _ModMeta(
            mod_atype=mod_atype,
            mod_class=mod_class,
            sub_mod_hashes=sub_mod_hashes,
            affix_type=affix_type,
            mod_tier=mod_tier
        )

    @classmethod
    def create_mod(cls, mod_atype: AType, mod_data: dict, mod_meta: _ModMeta, sub_mod_hash_to_text: dict):
        new_mod = ItemMod(
            atype=mod_atype,
            mod_class=mod_meta.mod_class,
            mod_name=mod_data['name'],
            affix_type=mod_meta.affix_type,
            mod_tier=mod_meta.mod_tier,
            mod_ilvl=int(mod_data['level'])
        )

        sub_mods = cls._create_sub_mods(
            sub_mod_hash_to_text=sub_mod_hash_to_text,
            mod_magnitudes=mod_data['magnitudes']
        )

        new_mod.insert_sub_mods(sub_mods)

        return new_mod


class _ModResolver:

    def __init__(self,
                 item_mods_file: ItemModsFile,
                 poe2db_injector: _PoE2DbInjector):
        self._poe2db_injector = poe2db_injector

        self._item_mods_file = item_mods_file
        self._mods = item_mods_file.load(default=dict())

    @staticmethod
    def _balance_same_hash_sub_mods(mods):
        sub_mods = [sub_mod for mod in mods for sub_mod in mod.sub_mods]

        sub_mod_hash_to_sub_mods = dict()
        for sub_mod in sub_mods:
            if sub_mod.sub_mod_hash not in sub_mod_hash_to_sub_mods:
                sub_mod_hash_to_sub_mods[sub_mod.sub_mod_hash] = []

            sub_mod_hash_to_sub_mods[sub_mod.sub_mod_hash].append(sub_mod)

        sub_mod_hash_to_sub_mods = {
            sub_mod_hash: sub_mods
            for sub_mod_hash, sub_mods in sub_mod_hash_to_sub_mods.items()
            if len(sub_mods) >= 2
        }
        for sub_mod_hash, sub_mods in sub_mod_hash_to_sub_mods.items():
            range_sums = []
            for sub_mod in sub_mods:
                range_sum = sum([sum(value_range) for value_range in sub_mod.values_ranges])
                range_sums.append(range_sum)

            ranges_total = sum(range_sums)
            range_portions = [range_sum/ranges_total for range_sum in range_sums]

            for i, sub_mod in enumerate(sub_mods):
                sub_mod.actual_values = [round(val * range_portions[i], 2) for val in sub_mod.actual_values]

    @log_errors(parse_log)
    def resolve_mods(self, rp: ApiResponseParser) -> list[ItemMod]:
        """
        Attempts to pull each mod in the item's data from file. Otherwise, it manages the mod's creation and caching
        :return: All mods from the item data
        """

        mods = []
        for mod_class in rp.mod_classes:
            mods_data = rp.fetch_mods_data(mod_class)
            for mod_data in mods_data:
                mod_meta = _ModFactory.create_mod_meta(
                    mod_class=mod_class,
                    mod_atype=rp.item_atype,
                    mod_data=mod_data
                )
                mod_id = mod_meta.mod_id
                sub_mod_hash_to_text = rp.fetch_sub_mod_hash_to_text(mod_class=mod_meta.mod_class)

                if mod_id in self._mods:
                    new_mod = copy.deepcopy(self._mods[mod_id])
                else:
                    parse_log.info(f"Could not find mod with ID {mod_id}. Creating and caching.")
                    new_mod = _ModFactory.create_mod(
                        mod_atype=mod_meta.mod_atype,
                        mod_data=mod_data,
                        mod_meta=mod_meta,
                        sub_mod_hash_to_text=sub_mod_hash_to_text
                    )
                    self._poe2db_injector.inject_poe2db_into_mod(mod=new_mod)

                    template_mod = copy.deepcopy(new_mod)
                    self._mods[mod_id] = template_mod

                # Mods are created as templates - which essentially just means that they have everything filled except
                # for actual values in their sub-mods
                _SubModValuesInjector.inject_sub_mod_values(
                    sub_mod_hash_to_text=sub_mod_hash_to_text,
                    current_mod=new_mod
                )
                mods.append(new_mod)

        """
         Individual mod texts on an item can be comprised of multiple different mods. The way mod creation
         works currently, those individual mods will all contain the TOTAL mod value as their mod value.
         We have to find those and balance them appropriately.
        """
        self._balance_same_hash_sub_mods(mods=mods)

        self._item_mods_file.save(data=self._mods)

        return mods


class _SkillsFactory:

    @staticmethod
    def create_skills(rp: ApiResponseParser) -> list[ItemSkill]:
        if not rp.skills_data:
            return []

        skills = []
        for skill_data in rp.skills_data:
            raw_skill = skill_data['values'][0]

            # Spear Throw is the only skill that is granted by an item without a level. May have to update in the future
            if raw_skill[0] == 'Spear Throw':
                new_skill = ItemSkill(
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

            new_skill = ItemSkill(
                name=skill_name,
                level=level
            )

            skills.append(new_skill)

        return skills
