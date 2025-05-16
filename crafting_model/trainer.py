
from stable-baselines3 import PPO
from stable-baselines3.common.env_checker import check_env

from . import environment

class RlTrainer:


    def __init__(self):
        self.env = environment.CraftingEnvironment()
        check_env(self.env)

        model = PPO("MultiInputPolicy", env, verbose=1)
        model.learn(total_timesteps=10000)

        # Save the model
        model.save("crafting_model")
