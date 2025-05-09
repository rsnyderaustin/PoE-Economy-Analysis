import json
import logging
from enum import Enum
from pathlib import Path
import pandas as pd

from instances_and_definitions import ItemMod, ModifiableListing
from . import utils


class FileKey(Enum):
    ATYPE_MODS = 'atype_mods'
    ATYPE_ENCODES = 'atype_encodes'
    BTYPE_ENCODES = 'btype_encodes'
    RARITY_ENCODES = 'rarity_encodes'
    CURRENCY_ENCODES = 'currency_encodes'
    CURRENCY_CONVERSIONS = 'currency_conversions'
    LISTING_FETCHES = 'listing_fetches'
    TRAINING_DATA = 'training_data'


class FilesManager:

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(FilesManager, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self.file_paths = {
            FileKey.ATYPE_MODS: Path.cwd() / 'file_management/files/atype_mods.json',
            FileKey.ATYPE_ENCODES: Path.cwd() / 'file_management/files/atype_encode.json',
            FileKey.BTYPE_ENCODES: Path.cwd() / 'file_management/files/btype_encode.json',
            FileKey.RARITY_ENCODES: Path.cwd() / 'file_management/files/rarity_encode.json',
            FileKey.CURRENCY_ENCODES: Path.cwd() / 'file_management/files/currency_encode.json',
            FileKey.CURRENCY_CONVERSIONS: Path.cwd() / 'file_management/files/currency_prices.csv',
            FileKey.LISTING_FETCHES: Path.cwd() / 'file_management/files/listing_fetch_dates.json',
            FileKey.TRAINING_DATA: Path.cwd() / 'file_management/files/listings.json'
        }

        self.file_data = dict()

        self._load_files()

    def _load_files(self):
        for key, path in self.file_paths.items():
            if path.exists:
                if path.suffix == '.json':
                    with open(path, 'r') as file:
                        self.file_data[key] = json.load(file)
                elif path.suffix == '.csv':
                    self.file_data[key] = pd.read_csv(path)

        self.file_data[FileKey.LISTING_FETCHES] = {
            date: set(listing_ids)
            for date, listing_ids in self.file_data[FileKey.LISTING_FETCHES].items()
        }

    def cache_mod(self, item_mod: ItemMod):
        mod_data = self.file_data[FileKey.ATYPE_MODS]
        if item_mod.atype not in mod_data:
            mod_data[item_mod.atype] = dict()

        atype_dict = mod_data[item_mod.atype]

        if item_mod.mod_id not in mod_data[item_mod.atype]:
            atype_dict[item_mod.mod_id] = {
                'mod_class': item_mod.mod_class.value,
                'sub_mod_ids': [sub_mod.mod_id for sub_mod in item_mod.sub_mods],
                'mod_types': item_mod.mod_types,
                'mod_texts': [sub_mod.sanitized_mod_text for sub_mod in item_mod.sub_mods],
                'affix_type': item_mod.affix_type.value if item_mod.affix_type else None, # Some mods don't have affix types
                'mod_tiers': dict()
            }

        mod_tiers_dict = atype_dict[item_mod.mod_id]['mod_tiers']

        if str(item_mod.mod_ilvl) not in mod_tiers_dict:
            mod_id_to_values_ranges = {
                sub_mod.mod_id: sub_mod.values_ranges
                for sub_mod in item_mod.sub_mods
            }
            mod_tiers_dict[item_mod.mod_ilvl] = {
                'ilvl': int(item_mod.mod_ilvl),
                'mod_id_to_values_ranges': mod_id_to_values_ranges,
                'weighting': item_mod.weighting
            }
            
    def cache_listings_data(self, listings: list[ModifiableListing]) -> bool:
        """
        :return: True if data was saved and files were exported
        """

        should_export = False
        for listing in listings:
            listing_dates = self.file_data[FileKey.LISTING_FETCHES]
            if listing.date_fetched not in listing_dates:
                listing_dates[listing.date_fetched] = set()
            listing_dates[listing.date_fetched].add(listing.date_fetched)

            atype_m = self.file_data[FileKey.ATYPE_ENCODES]
            if listing.item_atype not in atype_m:
                atype_m[listing.item_atype] = len(atype_m)
                should_export = True

            btype_e = self.file_data[FileKey.BTYPE_ENCODES]
            if listing.item_btype not in btype_e:
                btype_e[listing.item_btype] = len(btype_e)
                should_export = True

            rarity_e = self.file_data[FileKey.RARITY_ENCODES]
            if listing.rarity not in rarity_e:
                rarity_e[listing.rarity] = len(rarity_e)
                should_export = True

            currency_e = self.file_data[FileKey.CURRENCY_ENCODES]
            if listing.currency not in currency_e:
                currency_e[listing.currency] = len(currency_e)
                should_export = True

        if should_export:
            logging.info("New encode data - saving.")
            self.save_data()
            return True

        return False

    def cache_training_data(self, training_data: dict):
        self.file_data[FileKey.TRAINING_DATA] = training_data

    def save_data(self):
        logging.info("Exporting data.")
        for key, file_path in self.file_paths.items():
            utils.write_to_file(data=self.file_data[key], file_path=file_path)


