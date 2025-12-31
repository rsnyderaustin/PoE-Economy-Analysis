
from poe2db_scrape import Poe2DbScraper

from src.market_item_analysis.file_management.io_manager import Poe2DbModsManagerFile

poe2db_mods_manager = Poe2DbScraper().scrape()

Poe2DbModsManagerFile().save(data=poe2db_mods_manager)

