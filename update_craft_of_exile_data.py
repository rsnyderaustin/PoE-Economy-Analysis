
import logging

from craft_of_exile_api import CoEApiManager

logging.basicConfig(level=logging.INFO,
                    force=True)


coe_data = CoEApiManager().pull_data(endpoint='bases',
                                     load_locally=True)
coe_mods = CoEApiManager().pull_data(endpoint='mods',
                                     load_locally=True)
