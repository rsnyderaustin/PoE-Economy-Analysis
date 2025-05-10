import logging
from datetime import datetime
import pandas as pd

import file_management
from file_management import FileKey
from instances_and_definitions import ModifiableListing
from shared import shared_utils
from . import utils


def _determine_dict_length(data: dict):
    return max([len(v) for v in data.values()])


def _flatten_listing_properties(listing: ModifiableListing) -> dict:
    flattened_properties = dict()
    for property_name, property_values in listing.item_properties.items():
        flattened_properties[property_name] = 0
        for v in property_values:
            if isinstance(v, int) or isinstance(v, float):
                flattened_properties[property_name] += v
            elif len(v) == 2:
                flattened_properties[property_name] += ((v[0] + v[1]) / 2)
            elif len(v) == 1:
                flattened_properties[property_name] += v[0]
            else:
                raise ValueError(f"Property value {property_values} has unexpected structure.")

    return flattened_properties


class PricePredictDataManager:
    _replaced_attribute_cols = [
        'Attacks per Second',
        'Physical Damage',
        'Cold Damage',
        'Fire Damage',
        'Lightning Damage'
    ]

    _local_weapon_mod_cols = [
        'adds_#_to_#_fire_damage',
        '#%_increased_attack_speed',
        '#%_increased_physical_damage',
        'adds_#_to_#_cold_damage',
        'adds_#_to_#_lightning_damage',
        'adds_#_to_#_physical_damage',
        '+#.#%_to_critical_hit_chance',
        '+#%_to_critical_hit_chance',
        '#% increased Physical Damage',
        'Adds # to # Fire Damage',
        'Adds # to # Lightning Damage',
        'Adds # to # Cold Damage',
        '#% increased Attack Speed',
        'Quality'
    ]

    _select_remove_cols = [
        'open_prefixes',
        'open_suffixes',
        'minutes_since_listed',
        'minutes_since_league_start'
    ]

    _aggregate_remove_cols = [
        *_replaced_attribute_cols,
        *_local_weapon_mod_cols,
        *_select_remove_cols
    ]

    _model_category_cols = [
        'atype',
        'btype',
        'rarity',
        'corrupted',
        'identified'
    ]

    def __init__(self):
        self.currency_convert = shared_utils.CurrencyConverter()

        files_manager = file_management.FilesManager()
        self.training_data = files_manager.file_data[FileKey.CRITICAL_PRICE_PREDICT_TRAINING]
        self.training_data_length = _determine_dict_length(self.training_data)

        self.market_data = {col: [] for col in self.training_data.keys()} if self.training_data else dict()
        files_manager.file_data[FileKey.MARKET_SCAN] = self.market_data

        self.market_data_length = 0

    def _flatten_listing_import(self, listing: ModifiableListing) -> dict:
        flattened_properties = _flatten_listing_properties(listing)
        dt_date_fetched = datetime.strptime(listing.date_fetched, "%Y-%m-%dT%H:%M:%SZ")
        exalts_price = self.currency_convert.convert_to_exalts(currency=listing.currency,
                                                               currency_amount=listing.currency_amount,
                                                               relevant_date=dt_date_fetched)

        flattened_data = {
            'minutes_since_listed': listing.minutes_since_listed,
            'minutes_since_league_start': listing.minutes_since_league_start,
            'exalts': exalts_price,
            'open_prefixes': listing.open_prefixes,
            'open_suffixes': listing.open_suffixes,
            'atype': listing.item_atype,
            'btype': listing.item_btype,
            'rarity': listing.rarity,
            'corrupted': str(listing.corrupted),
            **flattened_properties
        }

        # Split up hybrid mods and average their value ranges. No known value ranges are not averageable
        summed_sub_mods = utils.sum_sub_mod_values(listing)
        flattened_data.update(summed_sub_mods)

        skills_dict = {item_skill.name: item_skill.level for item_skill in listing.item_skills}
        flattened_data.update(skills_dict)

        flattened_data['max_quality_pdps'] = utils.calculate_max_quality_pdps(flattened_data)
        flattened_data['edps'] = utils.calculate_elemental_dps(flattened_data)

        for col in [*self.__class__._aggregate_remove_cols]:
            flattened_data.pop(col, None)

        # Some columns have just one letter - not sure why but need to find out
        for col, values in flattened_data.items():
            if len(col) == 1:
                logging.error(f"Found 1 length attribute name for listing {listing.__dict__}")
                flattened_data.pop(col)

        return flattened_data

    def cache_training_data(self, training_listings: list[ModifiableListing]):
        for training_listing in training_listings:
            training_data = self._flatten_listing_import(training_listing)
            for col, value in training_data.items():
                if col not in self.training_data:
                    self.training_data[col] = [None for _ in list(range(self.training_data_length))]
                self.training_data[col].append(value)

            leftover_cols = [col for col in self.training_data.keys() if col not in training_data.keys()]

            for col in leftover_cols:
                self.training_data[col].append(None)

    def cache_market_data(self, market_listings: list[ModifiableListing]):
        for market_listing in market_listings:
            market_data = self._flatten_listing_import(market_listing)
            if not self.market_data:
                # If search data is empty then our only hope is filling column structure from training data
                if self.training_data:
                    self.market_data = {col: [] for col in self.training_data.keys()}
                else:
                    raise ValueError(f"Cannot add PricePredict market scan data. No training data to determine column structure.")

            for col, value in market_data.items():
                if col not in self.market_data:
                    raise KeyError(f"Column {col} not in PricePredict market scan data. All columns from training data must be "
                                   f"present when adding data.")
                self.market_data[col].append(value)

            leftover_cols = [col for col in self.market_data.keys() if col not in market_data.keys()]

            for col in leftover_cols:
                self.market_data[col].append(None)

    def export_data_for_model(self, which_file: FileKey) -> pd.DataFrame:
        if which_file == FileKey.CRITICAL_PRICE_PREDICT_TRAINING:
            data = self.training_data
        elif which_file == FileKey.MARKET_SCAN:
            data = self.market_data
        else:
            raise ValueError(f"Received incompatible FileKey {which_file}")

        df = pd.DataFrame(data)

        for category_col in self.__class__._model_category_cols:
            if category_col in df.columns:
                df[category_col] = df[category_col].astype("category")

        # Keep only numerical columns (int64 & float64)
        df = df.select_dtypes(include=['int64', 'float64'])

        # Fill NaN values with 0
        df.fillna(0, inplace=True)

        return df



