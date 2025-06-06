from file_management.file_managers import OfficialStatsFile, OfficialStaticFile
from official_poe_api import OfficialApiPuller, OfficialEndpoint

api_m = OfficialApiPuller()

static = api_m.pull_data(OfficialEndpoint.STATIC)
stats = api_m.pull_data(OfficialEndpoint.STATS)

OfficialStatsFile().save(data=stats)
OfficialStaticFile().save(data=static)

