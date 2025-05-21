import copy
import pprint
import random

import gymnasium as gym
from gymnasium import spaces

import crafting
from crafting import *
from . import utils


def create_observation(listing) -> dict:
    obs = {
        'atype': listing.item_atype,
        'rarity': listing.rarity,
        'ilvl': listing.ilvl,
        'corrupted': listing.corrupted,
        'identified': listing.identified,
        'implicit_mods': utils.format_mods_into_dict(listing.implicit_mods),
        'enchant_mods': utils.format_mods_into_dict(listing.enchant_mods),
        'fractured_mods': utils.format_mods_into_dict(listing.fractured_mods),
        'explicit_mods': utils.format_mods_into_dict(listing.explicit_mods),
        'item_skills': utils.format_skills_into_dict(listing.item_skills),
        'properties': listing.item_properties
    }

    return obs


def log_action(action: str, done: bool, cost: float, original_price: float, predicted_price: float, reward: float, message: str,
               listing_data: dict = None):
    logging.info(f"\n---- New Action ----"
                 f"\nAction: {action}"
                 f"\nDone crafting: {done}"
                 f"\nAction cost: {cost}"
                 f"\nOriginal price: {original_price}"
                 f"\nPredicted price: {predicted_price}"
                 f"\nAction reward: {reward}"
                 f"\nMessage: {message}"
                 f"\nListing data (Optional): {pprint.pprint(listing_data)}")


class CraftingEnvironment(gym.Env):

    def __init__(self, listing: ModifiableListing, price_predictor, exalts_budget):
        super(CraftingEnvironment, self).__init__()

        self.exalts_budget = exalts_budget

        self.original_state = copy.deepcopy(listing)
        self.original_price = price_predictor.predict_price(listing=listing)

        self.listing = listing
        self.current_price = self.original_price

        self.crafting_engine = crafting.CraftingEngine()
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

        self.observation_space = spaces.Dict({})

        self.total_exalts_spent = 0

    def _handle_stop_action(self) -> tuple:
        revenue = self.current_price
        cost = self.original_price + self.total_exalts_spent
        percent_profit = (revenue - cost) / cost
        is_done = True
        return create_observation(self.listing), percent_profit, is_done, {}

    def _handle_currency_engine_action(self, action) -> tuple:
        done = False
        currency = self.currency_map[action]
        currency_cost = shared.currency_converter.convert_to_exalts(currency=str(currency),
                                                                    currency_amount=1)

        if self.total_exalts_spent + currency_cost > self.exalts_budget:
            reward = -1
            done = True
            log_action(action=str(action), done=done, cost=currency_cost, original_price=self.current_price,
                       predicted_price=self.current_price, reward=reward, message="Exceeded budget.",
                       listing_data=self.listing.__dict__)
            return create_observation(self.listing), reward, done, {}

        self.total_exalts_spent += currency_cost

        outcomes = currency.apply(crafting_engine=self.crafting_engine,
                                  listing=self.listing)

        if len(outcomes) == 1 and outcomes[0] is StaticOutcome.NO_CHANGE:
            reward = -1
            log_action(action=str(action), done=done, cost=currency_cost, original_price=self.current_price,
                       predicted_price=self.current_price, reward=reward, message="No change on item.",
                       listing_data=self.listing.__dict__)
            return create_observation(self.listing), reward, done, {}

        random_outcome = random.choices(outcomes,
                                        weights=[outcome.probability for outcome in outcomes],
                                        k=1)[0]
        self.listing = self.crafting_engine.apply_crafting_outcome(listing=self.listing,
                                                                   outcome=random_outcome)

        predicted_price = self.price_predictor.predict_price(listing=self.listing)

        revenue = predicted_price
        cost = self.original_price + self.total_exalts_spent
        percent_profit = (revenue - cost) / cost
        reward = percent_profit

        obs = create_observation(self.listing)

        log_action(action=str(action), done=done, cost=currency_cost, original_price=self.current_price,
                   predicted_price=self.current_price, reward=reward, message="No change on item.")
        return obs, percent_profit, done, {}

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
        return create_observation(self.listing)
