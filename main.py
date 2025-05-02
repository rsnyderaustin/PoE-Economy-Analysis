
import logging

from external_apis.craft_of_exile_api import CoEDataPuller, CoEEndpoint

logging.basicConfig(level=logging.INFO,
                    force=True)

coe_data = CoEDataPuller.pull_data(endpoint=CoEEndpoint.BASE_TYPES)
coe_mods = CoEDataPuller.pull_data(endpoint=CoEEndpoint.MODS_AND_WEIGHTS)
x=0
