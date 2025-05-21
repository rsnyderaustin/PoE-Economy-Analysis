import copy

import gymnasium as gym
from gymnasium import spaces
import numpy as np
import random

import crafting
from crafting import *
from . import utils


class CraftingEnvironment(gym.Env):

    def __init__(self, listing, price_predictor, exalts_budget):
        super(CraftingEnvironment, self).__init__()

        self.exalts_budget = exalts_budget

        self.original_state = copy.deepcopy(listing)
        self.original_price = price_predictor.predict_price(listing=listing)

        self.listing = listing
        self.current_price = self.original_price

        self.crafting_engine = crafting.CraftingEngine()
        self.price_predictor = price_predictor

        self.action_space = spaces.Discrete(14)

        self.currency_map = {
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
            12: crafting.OrbOfTransmutation
        }

        self.observation_space = spaces.Dict({})

    def _create_observation(self) -> dict:
        obs = {
            'atype': self.listing.item_atype,
            'rarity': self.listing.rarity,
            'ilvl': self.listing.ilvl,
            'corrupted': self.listing.corrupted,
            'identified': self.listing.identified,
            'implicit_mods': utils.format_mods_into_dict(self.listing.implicit_mods),
            'enchant_mods': utils.format_mods_into_dict(self.listing.enchant_mods),
            'fractured_mods': utils.format_mods_into_dict(self.listing.fractured_mods),
            'explicit_mods': utils.format_mods_into_dict(self.listing.explicit_mods),
            'item_skills': utils.format_skills_into_dict(self.listing.item_skills),
            'properties': self.listing.item_properties
        }

        return obs

    def step(self, action):
        currency = self.currency_map[action]
        currency_cost = shared.currency_converter.convert_to_exalts(currency=str(currency),
                                                                    currency_amount=1)
        outcomes = currency.apply(crafting_engine=self.crafting_engine,
                                  listing=self.listing)

        random_outcome = random.choices(outcomes,
                                        weights=[outcome.probability for outcome in outcomes],
                                        k=1)[0]
        self.listing = self.crafting_engine.apply_crafting_outcome(listing=self.listing,
                                                                   outcome=random_outcome)

        predicted_price = self.price_predictor.predict_price(listing=self.listing)

        reward = predicted_price - self.current_price - currency_cost
        self.current_price = predicted_price

        obs = self._create_observation()

        return obs, reward, True, {}

    def reset(self):
        self.listing = copy.deepcopy(self.original_state)
        self.current_price = self.original_price
