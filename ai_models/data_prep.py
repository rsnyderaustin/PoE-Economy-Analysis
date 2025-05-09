
import pandas as pd

from file_management import FilesManager, FileKey
from instances_and_definitions import ModifiableListing
from . import utils


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
            

class DataPrep:

    def __init__(self):
        self.files_manager = FilesManager()
        self.training_data = self.files_manager.file_data[FileKey.TRAINING_DATA]

        self.currency_to_exalts = utils.fetch_currency_to_conversion(
            conversions_data=self.files_manager.file_data[FileKey.CURRENCY_CONVERSIONS]
        )

        self.num_rows = max(len(v_list) for v_list in self.training_data.values()) if self.training_data else 0

    def format_listing_for_price_prediction(self, listing: ModifiableListing) -> dict:
        flattened_listing = self._flatten_listing(listing)
        flattened_listing['max_quality_pdps'] = _calculate_max_quality_pdps(flattened_listing)
        flattened_listing['edps'] = _calculate_elemental_dps(flattened_listing)

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
            flattened_listing.pop(col, None)

        for col, values in flattened_listing.items():
            if len(col) == 1:
                flattened_listing.pop(col)

        return flattened_listing

    def _convert_currency_to_exalt(self, currency, amount):
        if currency in self.currency_to_exalts:
            exalts_price = amount * self.currency_to_exalts[currency]
        elif currency == 'exalted':
            exalts_price = amount
        else:
            raise ValueError(f"Currency {currency} not supported.")

        return exalts_price

    def _flatten_listing(self, listing: ModifiableListing):
        # Make a dict that averages out the property values if they're a range, otherwise just give us the number
        flattened_properties = _flatten_listing_properties(listing)

        exalts_price = self._convert_currency_to_exalt(currency=listing.currency,
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

        return flattened_data

    def prepare_price_prediction_data_for_model(self) -> pd.DataFrame:
        df = pd.DataFrame(self.training_data)

        df['atype'] = df['atype'].astype("category")
        df['rarity'] = df['rarity'].astype("category")
        df['corrupted'] = df['corrupted'].astype("category")

        # Keep only numerical columns (int64 & float64)
        df = df.select_dtypes(include=['int64', 'float64'])

        # Fill NaN values with 0
        df.fillna(0, inplace=True)

        return df
