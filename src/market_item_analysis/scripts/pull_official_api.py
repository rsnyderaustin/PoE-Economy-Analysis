from src.market_item_analysis.file_management.io_manager import OfficialStatsFile, OfficialStaticFile
from src.market_item_analysis.official_poe_api import OfficialApiPuller, OfficialEndpoint

api_m = OfficialApiPuller()

static = api_m.pull_data(OfficialEndpoint.STATIC)
stats = api_m.pull_data(OfficialEndpoint.STATS)

OfficialStatsFile().save(data=stats)
OfficialStaticFile().save(data=static)

