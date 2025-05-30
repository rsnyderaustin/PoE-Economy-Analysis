from file_management import FilesManager, DataPath
from poe2db_scrape import Poe2DbScraper

fm = FilesManager()
poe2db_mods_manager = Poe2DbScraper().scrape()
fm.cache_data(DataPath.POE2DB_MODS_MANAGER, data=poe2db_mods_manager)
fm.save_data(paths=[DataPath.POE2DB_MODS_MANAGER])


