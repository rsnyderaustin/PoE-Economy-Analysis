
from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env

import file_management
from file_management import FileKey
from . import environment


class RlTrainer:

    @classmethod
    def train(cls, listing):
        price_predictor = file_management.FilesManager().model_data[FileKey.PRICE_PREDICT_MODEL]
        env = environment.CraftingEnvironment(listing=listing,
                                              price_predictor=price_predictor)
        check_env(env)

        model = PPO("MultiInputPolicy", env, verbose=1)
        model.learn(total_timesteps=10000)

        # Save the model
        model.save("crafting_model")
