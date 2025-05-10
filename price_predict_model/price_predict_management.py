import logging

import pandas as pd

from file_management import FilesManager, FileKey
from instances_and_definitions import ModifiableListing
from . import utils
from .data_management import PricePredictDataManager


def _calculate_max_quality_pdps(listing_data: dict):
    quality = listing_data.get('Quality', 0)
    damage = listing_data.get('Physical Damage', 0)
    attacks_per_second = listing_data.get('Attacks per Second', 0)

    current_multiplier = 1 + (quality / 100)
    max_multiplier = 1.20

    # Calculate the base damage and then the 20% quality damage
    base_damage = damage / current_multiplier
    max_quality_damage = base_damage * max_multiplier

    max_quality_pdps = max_quality_damage * attacks_per_second
    return max_quality_pdps


def _calculate_elemental_dps(listing_data: dict):
    cold_damage = listing_data.get('Cold Damage', 0)
    fire_damage = listing_data.get('Fire Damage', 0)
    lightning_damage = listing_data.get('Lightning Damage', 0)
    attacks_per_second = listing_data.get('Attacks per Second', 0)

    edps = (cold_damage + fire_damage + lightning_damage) * attacks_per_second
    return edps


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
            

class PricePredictManager:

    def __init__(self):
        self.files_manager = FilesManager()

        self.data_manager = PricePredictDataManager()

        self.currency_to_exalts = utils.fetch_currency_to_conversion(
            conversions_data=self.files_manager.file_data[FileKey.CURRENCY_CONVERSIONS]
        )

        t_data = self.files_manager.file_data[FileKey.CRITICAL_PRICE_PREDICT_TRAINING]
        pp_data = self.files_manager.file_data[FileKey.PRICE_PREDICT]
        self.num_rows = {
            FileKey.CRITICAL_PRICE_PREDICT_TRAINING: max(len(v_list) for v_list in t_data.values()) if t_data else 0,
            FileKey.PRICE_PREDICT: max(len(v_list) for v_list in pp_data.values()) if pp_data else 0
        }

    def _format_listing_for_price_prediction(self, listing: ModifiableListing) -> dict:
        flattened_properties = _flatten_listing_properties(listing)

        exalts_price = self.convert_currency_to_exalt(currency=listing.currency,
                                                      amount=listing.currency_amount)

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
        
        flattened_data['max_quality_pdps'] = _calculate_max_quality_pdps(flattened_data)
        flattened_data['edps'] = _calculate_elemental_dps(flattened_data)

        replaced_attributes = [
            'Attacks per Second',
            'Physical Damage',
            'Cold Damage',
            'Fire Damage',
            'Lightning Damage'
        ]

        local_weapon_mods = [
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

        select_cols = [
            'open_prefixes',
            'open_suffixes',
            'minutes_since_listed',
            'minutes_since_league_start'
        ]

        for col in [*replaced_attributes, *local_weapon_mods, *select_cols]:
            flattened_data.pop(col, None)

        # Some columns have just one letter - not sure why
        for col, values in flattened_data.items():
            if len(col) == 1:
                flattened_data.pop(col)

        return flattened_data

    def convert_currency_to_exalt(self, currency, amount):
        if currency in self.currency_to_exalts:
            exalts_price = amount * self.currency_to_exalts[currency]
        elif currency == 'exalted':
            exalts_price = amount
        else:
            raise ValueError(f"Currency {currency} not supported.")

        return exalts_price

    def prepare_price_predict_data_for_model(self, which_file: FileKey) -> pd.DataFrame:
        data = self.files_manager.file_data[which_file]
        df = pd.DataFrame(data)

        df['atype'] = df['atype'].astype("category")
        df['rarity'] = df['rarity'].astype("category")
        df['corrupted'] = df['corrupted'].astype("category")

        # Keep only numerical columns (int64 & float64)
        df = df.select_dtypes(include=['int64', 'float64'])

        # Fill NaN values with 0
        df.fillna(0, inplace=True)

        return df

    def save_listings(self, listings: list[ModifiableListing], which_file: FileKey):
        data = self.files_manager.file_data[which_file]
        for listing in listings:
            flattened_listing = self._format_listing_for_price_prediction(listing)

            if which_file == FileKey.CRITICAL_PRICE_PREDICT_TRAINING:
            for col_name, value in flattened_listing.items():
                if col_name not in data:
                    # We have to insert a value for each row since this column has been added
                    data[col_name] = [None for _ in list(range(self.num_rows[which_file]))]
                data[col_name].append(value)

            # Append a new value for each column that wasn't a part of this listing data
            non_included_data_cols = [col for col in set(data.keys()) if col not in set(flattened_listing.keys())]
            for col_name in non_included_data_cols:
                data[col_name].append(None)

            self.num_rows[which_file] += 1

        self.files_manager.file_data[which_file] = data

