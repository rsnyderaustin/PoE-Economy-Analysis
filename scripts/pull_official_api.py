from file_management import DataPath, FilesManager
from official_poe_api import OfficialApiPuller, OfficialEndpoint

fm = FilesManager()

api_m = OfficialApiPuller()

static = api_m.pull_data(OfficialEndpoint.STATIC)
stats = api_m.pull_data(OfficialEndpoint.STATS)

fm.cache_data(data_path=DataPath.OFFICIAL_STATIC, data=static)
fm.cache_data(data_path=DataPath.OFFICIAL_STATS, data=stats)

fm.save_data(paths=[DataPath.OFFICIAL_STATIC, DataPath.OFFICIAL_STATS])

