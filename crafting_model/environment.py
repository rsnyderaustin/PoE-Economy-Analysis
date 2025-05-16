import copy

import gym
from gym import spaces
import numpy as np
import random

import crafting
from crafting import *
from . import utils


class CraftingEnvironment(gym.Env):

    def __init__(self, listing, price_predictor):
        super(CraftingEnvironment, self).__init__()

        self.original_state = copy.deepcopy(listing)
        self.original_price = price_predictor.predict_price(listing=listing)

        self.listing = listing
        self.current_price = self.original_price

        self.crafting_engine = crafting.CraftingEngine()
        self.price_predictor = price_predictor

        self.action_space = spaces.Discrete(14)
        self.observation_space = spaces.Dict({

        })

    def step(self, action):
        if action == 0:
            outcomes = crafting.ArcanistsEtcher.apply(self.crafting_engine,
                                                      listing=self.listing)
        elif action == 1:
            outcomes = crafting.ArmourersScrap.apply(self.crafting_engine,
                                                     listing=self.listing)
        elif action == 2:
            outcomes = crafting.ArtificersOrb.apply(self.crafting_engine,
                                                    listing=self.listing)
        elif action == 3:
            outcomes = crafting.BlacksmithsWhetstone.apply(self.crafting_engine,
                                                           listing=self.listing)
        elif action == 4:
            outcomes = crafting.ChaosOrb.apply(self.crafting_engine,
                                               listing=self.listing)
        elif action == 5:
            outcomes = crafting.ExaltedOrb.apply(self.crafting_engine,
                                                 listing=self.listing)
        elif action == 6:
            outcomes = crafting.FracturingOrb.apply(self.crafting_engine,
                                                    listing=self.listing)
        elif action == 7:
            outcomes = crafting.GemcuttersPrism.apply(self.crafting_engine,
                                                      listing=self.listing)
        elif action == 8:
            outcomes = crafting.GlassblowersBauble.apply(self.crafting_engine,
                                                         listing=self.listing)
        elif action == 9:
            outcomes = crafting.OrbOfAlchemy.apply(self.crafting_engine,
                                                   listing=self.listing)
        elif action == 10:
            outcomes = crafting.OrbOfAnnulment.apply(self.crafting_engine,
                                                     listing=self.listing)
        elif action == 11:
            outcomes = crafting.OrbOfAugmentation.apply(self.crafting_engine,
                                                        listing=self.listing)
        elif action == 12:
            outcomes = crafting.OrbOfTransmutation.apply(self.crafting_engine,
                                                         listing=self.listing)

        random_outcome = random.choices(outcomes,
                                        weights=[outcome.probability for outcome in outcomes],
                                        k=1)
        self.crafting_engine.apply_crafting_outcome(listing=self.listing,
                                                    outcome=random_outcome)

        predicted_price = self.price_predictor.predict_price(listing=self.listing)

        reward = predicted_price - self.current_price

        obs = {
            'atype': self.listing.atype,
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

        return obs, reward, True, {}

    def reset(self):
        self.listing = copy.deepcopy(self.original_state)
        self.current_price = self.original_price



