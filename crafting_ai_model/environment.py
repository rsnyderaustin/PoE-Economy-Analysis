import copy
import pprint
import random
from dataclasses import dataclass
from typing import Any

import gymnasium as gym
import numpy as np

import crafting
from crafting import *
from instances_and_definitions import ItemMod, ItemSkill
from shared import ModClass
from price_predict_ai_model import PricePredictor


def log_action(action: str, done: bool, original_price: float, predicted_price: float, message: str,
               cost: float = None, reward: float = None, listing_data: dict = None):
    logging.info(f"\n---- New Action ----"
                 f"\nAction: {action}"
                 f"\nDone crafting: {done}"
                 f"\nAction cost: {cost}"
                 f"\nOriginal price: {original_price}"
                 f"\nPredicted price: {predicted_price}"
                 f"\nAction reward: {reward}"
                 f"\nMessage: {message}"
                 f"\nListing data (Optional): {pprint.pprint(listing_data)}")


@dataclass
class SpaceItemDetail:
    item_id: str
    item: Any
    index_range: tuple


class ObservationSpace:
    _space_cache = dict()

    listing_attributes = [
        'minutes_since_league_start',
        'item_atype',
        'rarity',
        'ilvl',
        'identified',
        'corrupted',
        'edps',
        'max_quality_pdps'
    ]

    calculated_attributes = [
        'edps',
        'max_quality_pdps'
    ]

    def __init__(self,
                 max_skills: int = 3,
                 max_implicits: int = 3,
                 max_values_per_implicit: int = 3,
                 max_enchants: int = 5,
                 max_values_per_enchant: int = 2,
                 max_fractured: int = 2,
                 max_values_per_fractured: int = 3,
                 max_explicits: int = 6,
                 max_values_per_explicit: int = 3):
        _cache_key = (max_skills, max_implicits, max_values_per_implicit, max_enchants, max_values_per_enchant,
                      max_fractured, max_values_per_fractured, max_explicits, max_values_per_explicit)
        if _cache_key in self.__class__._space_cache:
            self._space = copy.deepcopy(self.__class__._space_cache[_cache_key])
        else:
            _base_space = dict()

            _base_space.update(
                self._determine_skills_shape(max_skills=max_skills)
            )

            _base_space.update(
                self._determine_mods_shape(max_mods=max_implicits,
                                           max_values=max_values_per_implicit,
                                           mod_class=ModClass.IMPLICIT)
            )
            _base_space.update(
                self._determine_mods_shape(max_mods=max_enchants,
                                           max_values=max_values_per_enchant,
                                           mod_class=ModClass.ENCHANT)
            )
            _base_space.update(
                self._determine_mods_shape(max_mods=max_fractured,
                                           max_values=max_values_per_fractured,
                                           mod_class=ModClass.FRACTURED)
            )
            _base_space.update(
                self._determine_mods_shape(max_mods=max_explicits,
                                           max_values=max_values_per_explicit,
                                           mod_class=ModClass.EXPLICIT)
            )

            _base_space.update(
                {att: None for att in self.__class__.listing_attributes}
            )

            self.__class__._space_cache[_cache_key] = _base_space
            self._space = copy.deepcopy(_base_space)

        self._key_to_index = {k: i for i, k in enumerate(self._space.keys())}  # For determining indices with keys (adding elements)
        self._index_to_key = {i: k for i, k in enumerate(self._space.keys())}  # For determining keys with indices (removing elements)

        self.num_mods = {
            ModClass.IMPLICIT: 0,
            ModClass.ENCHANT: 0,
            ModClass.FRACTURED: 0,
            ModClass.EXPLICIT: 0
        }

        self.max_mods = {
            ModClass.IMPLICIT: max_implicits,
            ModClass.ENCHANT: max_enchants,
            ModClass.FRACTURED: max_fractured,
            ModClass.EXPLICIT: max_explicits
        }

        self.max_values = {
            ModClass.IMPLICIT: max_values_per_implicit,
            ModClass.ENCHANT: max_values_per_enchant,
            ModClass.FRACTURED: max_values_per_fractured,
            ModClass.EXPLICIT: max_values_per_explicit
        }

        self.num_skills = 0
        self.max_skills = max_skills

    @property
    def shape(self) -> int:
        return len(self._space)

    @staticmethod
    def _create_mod_id_key(mod_class: ModClass, mod_i: int) -> str:
        return f"{mod_class.value}_{mod_i}_id"

    @staticmethod
    def _create_affix_key(mod_class: ModClass, mod_i: int) -> str:
        return f"{mod_class.value}_{mod_i}_affix_type"

    @staticmethod
    def _create_mod_value_key(mod_class: ModClass, mod_i: int, value_i: int) -> str:
        return f"{mod_class.value}_{mod_i}_value_{value_i}"

    @staticmethod
    def _create_skill_name_key(skill_i: int):
        return f"skill_{skill_i}_name"

    @staticmethod
    def _create_skill_level_key(skill_i: int):
        return f"skill_{skill_i}_level"

    @classmethod
    def _determine_mods_shape(cls, max_mods: int, max_values: int, mod_class: ModClass) -> dict:
        shape = dict()
        for mod_i in list(range(max_mods)):
            mod_id_key = cls._create_mod_id_key(mod_class=mod_class, mod_i=mod_i)
            shape[mod_id_key] = None
            if mod_class in [ModClass.EXPLICIT, ModClass.FRACTURED]:
                affix_type_key = cls._create_affix_key(mod_class=mod_class, mod_i=mod_i)
                shape[affix_type_key] = None
            for value_i in list(range(max_values)):
                mod_value_key = cls._create_mod_value_key(mod_class=mod_class, mod_i=mod_i, value_i=value_i)
                shape[mod_value_key] = None
        return shape

    @classmethod
    def _determine_skills_shape(cls, max_skills: int) -> dict:
        shape = dict()
        for skill_i in list(range(max_skills)):
            skill_name_key = cls._create_skill_name_key(skill_i)
            shape[skill_name_key] = None

            skill_level_key = cls._create_skill_level_key(skill_i)
            shape[skill_level_key] = None

        return shape

    def add_skill(self, skill: ItemSkill):
        if self.num_skills + 1 > self.max_skills:
            raise ValueError(f"Reached past the skills limit of {self.max_skills}.")

        skill_i = self.num_skills
        name_key = self._create_skill_name_key(skill_i)
        self._space[name_key] = skill.name

        level_key = self._create_skill_level_key(skill_i)
        self._space[level_key] = skill.level

    def add_mod(self, mod: ItemMod):
        num_mods = self.num_mods[mod.mod_class_e]

        if num_mods + 1 > self.max_mods[mod.mod_class_e]:
            raise ValueError(f"Reached past the observation space limit for mod class {mod.mod_class_e}")

        mod_i = num_mods
        mod_id_key = self._create_mod_id_key(mod_class=mod.mod_class_e, mod_i=mod_i)
        self._space[mod_id_key] = mod.mod_id

        if mod.mod_class_e in [ModClass.EXPLICIT, ModClass.FRACTURED]:
            affix_key = self._create_affix_key(mod_class=mod.mod_class_e, mod_i=mod_i)
            self._space[affix_key] = mod.affix_type_e.value

        mod_values = [actual_value for sub_mod in mod.sub_mods for actual_value in sub_mod.actual_values]

        if len(mod_values) > self.max_values[mod.mod_class_e]:
            raise ValueError(f"Too many values in mod {mod.mod_id} for slot {mod_i}")

        for value_i, mod_value in enumerate(mod_values):
            value_key = self._create_mod_value_key(mod_class=mod.mod_class_e, mod_i=mod_i, value_i=value_i)
            self._space[value_key] = mod_value

    def add_attributes(self, listing: ModifiableListing):
        attributes = {
            att: getattr(listing, att) for att in self.__class__.listing_attributes
        }
        self._space.update(attributes)

    def get(self) -> np.ndarray:
        return np.array(list(self._space.values()), dtype=np.float32)


class CraftingEnvironment(gym.Env):

    def __init__(self, listing: ModifiableListing, price_predictor: PricePredictor, exalts_budget):
        super(CraftingEnvironment, self).__init__()

        self.exalts_budget = exalts_budget

        self.original_state = copy.deepcopy(listing)
        self.original_price = price_predictor.predict_prices(listings=[listing])[0]

        self.listing = listing
        self.current_price = self.original_price

        self.price_predictor = price_predictor

        self.action_map = {
            0: crafting.ArcanistsEtcher,
            1: crafting.ArmourersScrap,
            2: crafting.ArtificersOrb,
            3: crafting.BlacksmithsWhetstone,
            4: crafting.ChaosOrb,
            5: crafting.ExaltedOrb,
            6: crafting.FracturingOrb,
            7: crafting.GemcuttersPrism,
            8: crafting.GlassblowersBauble,
            9: crafting.OrbOfAlchemy,
            10: crafting.OrbOfAnnulment,
            11: crafting.OrbOfAugmentation,
            12: crafting.OrbOfTransmutation,
            13: 'STOP'
        }

        self.total_exalts_spent = 0

    def _create_observation_space(self) -> np.ndarray:
        o = ObservationSpace()

        for skill in self.listing.item_skills:
            o.add_skill(skill)

        for mod in self.listing.mods:
            o.add_mod(mod)

        o.add_attributes(self.listing)

        return o.get()

    def _handle_stop_action(self) -> tuple:
        revenue = self.current_price
        cost = self.original_price + self.total_exalts_spent
        percent_profit = (revenue - cost) / cost
        done = True
        log_action(action='STOP', done=done, cost=None, original_price=self.current_price,
                   predicted_price=self.current_price, reward=None, message="Exceeded budget.",
                   listing_data=self.listing.__dict__)
        return self._create_observation_space(), percent_profit, done, {}

    def _handle_currency_engine_action(self, action) -> tuple:
        done = False
        currency = action
        currency_cost = shared.currency_converter.convert_to_exalts(currency=str(currency),
                                                                    currency_amount=1)

        # Return a small negative reward if we went over budget
        if self.total_exalts_spent + currency_cost > self.exalts_budget:
            reward = -1
            done = True
            log_action(action=str(currency), done=done, cost=currency_cost, original_price=self.current_price,
                       predicted_price=self.current_price, reward=reward, message="Exceeded budget.")
            return self._create_observation_space(), reward, done, {}

        self.total_exalts_spent += currency_cost

        outcome = currency.apply(crafting_engine=self.crafting_engine,
                                 listing=self.listing)

        if outcome == outcome.listing_changed:
            reward = -1
            log_action(action=str(currency), done=done, cost=currency_cost, original_price=self.current_price,
                       predicted_price=self.current_price, reward=reward, message="No change on item.",
                       listing_data=self.listing.__dict__)
            return self._create_observation_space(), reward, done, {}

        # If the outcome isn't NO_CHANGE, then it's just the new listing
        self.listing = outcome.new_listing

        predicted_price = self.price_predictor.predict_prices(listings=[self.listing])[0]

        revenue = predicted_price
        cost = self.original_price + self.total_exalts_spent
        percent_profit = (revenue - cost) / cost
        reward = percent_profit

        log_action(action=str(currency), done=done, cost=currency_cost, original_price=self.current_price,
                   predicted_price=self.current_price, reward=reward, message="No change on item.")
        return self._create_observation_space(), percent_profit, done, {}

    def step(self, action):
        action = self.action_map[action]

        if action == 'STOP':
            return self._handle_stop_action()
        elif isinstance(action, crafting.CurrencyEngine):
            return self._handle_currency_engine_action(action)

    def reset(self):
        self.listing = copy.deepcopy(self.original_state)
        self.current_price = self.original_price
        self.total_exalts_spent = 0
