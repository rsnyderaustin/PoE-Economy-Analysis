
from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env

from . import environment
from price_predict_ai_model import PricePredictor


class RlTrainer:

    @classmethod
    def train(cls,
              listing,
              price_predictor: PricePredictor,
              exalts_budget: int = 200,
              total_timesteps: int = 10000,
              crafting_model=None):
        env = environment.CraftingEnvironment(listing=listing,
                                              price_predictor=price_predictor,
                                              exalts_budget=exalts_budget)
        check_env(env)

        if crafting_model is None:
            crafting_model = PPO("MultiInputPolicy", env, verbose=1)

        crafting_model.set_env(env)
        crafting_model.learn(total_timesteps=total_timesteps)

        return crafting_model
