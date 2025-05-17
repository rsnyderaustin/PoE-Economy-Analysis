import logging
from datetime import datetime
from abc import ABC
import pandas as pd

import file_management
from file_management import FileKey
from instances_and_definitions import ModifiableListing
from shared import shared_utils, env_loader, currency_converter, EnvVariable
import shared
from . import utils
import psql


class ListingsClass(ABC):
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

    _aggregate_remove_cols = [
        *_replaced_attribute_cols,
        *_local_weapon_mod_cols
    ]

    _select_col_types = {
        'atype': 'category',
        'btype': 'category',
        'rarity': 'category',
        'identified': bool,
        'corrupted': bool
    }


class ListingFlattener(ListingsClass):

    @staticmethod
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

        flattened_properties = {utils.form_column_name(col): val for col, val in flattened_properties.items()}
        return flattened_properties

    @staticmethod
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

    @staticmethod
    def _calculate_elemental_dps(listing_data: dict):
        cold_damage = listing_data.get('Cold Damage', 0)
        fire_damage = listing_data.get('Fire Damage', 0)
        lightning_damage = listing_data.get('Lightning Damage', 0)
        attacks_per_second = listing_data.get('Attacks per Second', 0)

        edps = (cold_damage + fire_damage + lightning_damage) * attacks_per_second
        return edps

    @staticmethod
    def _sum_sub_mod_values(listing: ModifiableListing):
        summed_sub_mods = {}
        for mod in listing.mods:
            for sub_mod in mod.sub_mods:
                col_name = utils.form_column_name(sub_mod.sanitized_mod_text)
                if sub_mod.actual_values:
                    avg_value = sum(sub_mod.actual_values) / len(sub_mod.actual_values)
                    if sub_mod.mod_id not in summed_sub_mods:
                        summed_sub_mods[col_name] = avg_value
                    else:
                        summed_sub_mods[col_name] += avg_value
                else:
                    # If there is no value then it's just a static property (ex: "You cannot be poisoned"), and so
                    # we assign it a 1 to indicate to the model that it's an active mod
                    summed_sub_mods[col_name] = 1

        # Socketers are not consistently included enough to be considered in the listings data, so we just skip them
        """for socketer in listing.socketers:
            col_name = socketer.sanitized_socketer_text
            if socketer.actual_values:
                avg_value = sum(socketer.actual_values) / len(socketer.actual_values)
                if col_name not in summed_sub_mods:
                    summed_sub_mods[col_name] = avg_value
                else:
                    summed_sub_mods[col_name] += avg_value
            else:
                summed_sub_mods[col_name] = 1"""

        return summed_sub_mods

    @classmethod
    def flatten_listing(cls, listing: ModifiableListing) -> dict:
        flattened_properties = cls._flatten_listing_properties(listing)
        dt_date_fetched = datetime.strptime(listing.date_fetched, "%m-%d-%Y")
        exalts_price = shared.currency_converter.convert_to_exalts(currency=listing.currency,
                                                                   currency_amount=listing.currency_amount,
                                                                   relevant_date=dt_date_fetched)

        flattened_data = {
            'date_fetched': listing.date_fetched,
            'minutes_since_listed': listing.minutes_since_listed,
            'minutes_since_league_start': listing.minutes_since_league_start,
            'currency': listing.currency,
            'currency_amount': listing.currency_amount,
            'exalts': exalts_price,
            'open_prefixes': listing.open_prefixes,
            'open_suffixes': listing.open_suffixes,
            'atype': listing.item_atype,
            'ilvl': listing.ilvl,
            'category': listing.item_category.value,
            'rarity': listing.rarity,
            'corrupted': listing.corrupted,
            'identified': listing.identified,
            **flattened_properties
        }

        # Split up hybrid mods and average their value ranges. No known value ranges are not averageable
        summed_sub_mods = cls._sum_sub_mod_values(listing)
        flattened_data.update(summed_sub_mods)

        skills_dict = {item_skill.name: item_skill.level for item_skill in listing.item_skills}
        skills_dict = {utils.form_column_name(skill_name): lvl for skill_name, lvl in skills_dict.items()}
        flattened_data.update(skills_dict)

        flattened_data['max_quality_pdps'] = cls._calculate_max_quality_pdps(flattened_data)
        flattened_data['edps'] = cls._calculate_elemental_dps(flattened_data)

        for col in [*cls._aggregate_remove_cols]:
            flattened_data.pop(col, None)

        # Some columns have just one letter - not sure why but need to find out
        cols_to_remove = [col for col in flattened_data if len(col) == 1]
        for col in cols_to_remove:
            logging.error(f"Found 1-length attribute name {cols_to_remove} for listing {listing.__dict__}")
            flattened_data.pop(col)

        return flattened_data


class ListingsDataProcessor(ListingsClass):

    @staticmethod
    def flatten_listings_into_dict(listings: list[ModifiableListing]) -> dict:
        listings_data = dict()
        rows = 0
        for listing in listings:
            new_listing_data = ListingFlattener.flatten_listing(listing)

            new_cols = [col for col in new_listing_data if col not in listings_data]
            new_cols_dict = {col: [None] * rows for col in new_cols}
            listings_data.update(new_cols_dict)

            for col, val in new_listing_data.items():
                listings_data[col].append(val)

        return listings_data

    @classmethod
    def prepare_flattened_listings_data_for_model(cls, data: dict) -> pd.DataFrame:
        df = pd.DataFrame(data)

        select_dtype_cols = [col for col in cls._select_col_types if col in df.columns]
        for col in select_dtype_cols:
            dtype = cls._select_col_types[col]
            df[col] = df[col].astype(dtype)

        abnormal_type_cols = [col for col in df.columns
                              if col not in cls._select_col_types
                              and df[col].dtype not in ['int64', 'float64', 'bool', 'category']]
        for col in abnormal_type_cols:
            df[col] = df[col].astype('float64')

        df = df.select_dtypes(include=['int64', 'float64', 'bool', 'category'])

        return df
