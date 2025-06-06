
from file_management.file_managers import Poe2DbModsManagerFile
from poe2db_scrape import Poe2DbScraper

poe2db_mods_manager = Poe2DbScraper().scrape()

Poe2DbModsManagerFile().save(data=poe2db_mods_manager)

