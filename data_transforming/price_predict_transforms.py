import logging
from datetime import datetime
import pprint

from instances_and_definitions import ModifiableListing
from shared import shared_utils
from . import utils


select_col_types = {
    'atype': 'category',
    'btype': 'category',
    'rarity': 'category',
    'identified': bool,
    'corrupted': bool
}


class PricePredictTransformer:

    def __init__(self, listing: ModifiableListing):
        self.listing = listing
        self.data = dict()

    def _determine_date_fetched(self):
        return datetime.strptime(self.listing.date_fetched, "%m-%d-%Y")

    def insert_listing_properties(self):
        flattened_properties = dict()
        for property_name, property_values in self.listing.item_properties.items():
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

        flattened_properties = {shared_utils.form_column_name(col): val for col, val in flattened_properties.items()}
        self.data.update(flattened_properties)
        return self

    def insert_max_quality_pdps(self, column_name: str = 'max_quality_pdps'):
        quality = self.data.get('Quality', 0)
        damage = self.data.get('Physical Damage', 0)
        attacks_per_second = self.data.get('Attacks per Second', 0)

        current_multiplier = 1 + (quality / 100)
        max_multiplier = 1.20

        # Calculate the base damage and then the 20% quality damage
        base_damage = damage / current_multiplier
        max_quality_damage = base_damage * max_multiplier

        max_quality_pdps = max_quality_damage * attacks_per_second
        self.data[column_name] = max_quality_pdps
        return self

    def insert_elemental_dps(self, column_name: str = 'edps'):
        cold_damage = self.data.get('Cold Damage', 0)
        fire_damage = self.data.get('Fire Damage', 0)
        lightning_damage = self.data.get('Lightning Damage', 0)
        attacks_per_second = self.data.get('Attacks per Second', 0)

        edps = (cold_damage + fire_damage + lightning_damage) * attacks_per_second
        self.data[column_name] = edps
        return self

    def insert_metadata(self):
        metadata = {
            'date_fetched': self._determine_date_fetched(),
            'minutes_since_listed': self.listing.minutes_since_listed,
            'minutes_since_league_start': self.listing.minutes_since_league_start
        }
        self.data.update(metadata)
        return self

    def insert_currency_info(self):
        self.data['currency'] = self.listing.currency
        self.data['currency_amount'] = self.listing.currency_amount

        exalts_price = shared_utils.currency_converter.convert_to_exalts(
            currency=self.listing.currency,
            currency_amount=self.listing.currency_amount,
            relevant_date=self._determine_date_fetched()
        )
        self.data['exalts'] = exalts_price
        return self

    def insert_item_base_info(self):
        self.data['open_prefixes'] = self.listing.open_prefixes
        self.data['open_suffixes'] = self.listing.open_suffixes
        self.data['atype'] = self.listing.item_atype
        self.data['ilvl'] = self.listing.ilvl
        self.data['category'] = self.listing.item_category.value
        self.data['rarity'] = self.listing.rarity
        self.data['corrupted'] = self.listing.corrupted
        self.data['identified'] = self.listing.identified
        return self

    def insert_sub_mod_values(self):
        summed_sub_mods = {}
        for mod in self.listing.mods:
            for sub_mod in mod.sub_mods:
                col_name = shared_utils.form_column_name(sub_mod.sanitized_mod_text)
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

        self.data.update(summed_sub_mods)
        return self

    def insert_skills(self):
        skills_dict = {item_skill.name: item_skill.level for item_skill in self.listing.item_skills}
        skills_dict = {shared_utils.form_column_name(skill_name): lvl for skill_name, lvl in skills_dict.items()}
        self.data.update(skills_dict)
        return self

    def remove_local_mods(self):
        for local_mod_col in utils.local_weapon_mod_cols:
            self.data.pop(local_mod_col, None)
        return self

    def clean_columns(self):
        # Some columns have just one letter - not sure why but need to find out
        cols_to_remove = [col for col in self.data if len(col) == 1]
        for col in cols_to_remove:
            logging.error(f"Found 1-length attribute name {cols_to_remove} for listing: "
                          f"\n{pprint.pprint(self.listing.__dict__)}")
            self.data.pop(col)
        return self


def default_flatten_preset(listing: ModifiableListing) -> dict:
    return (
        PricePredictTransformer(listing)
        .insert_listing_properties()
        .insert_max_quality_pdps()
        .insert_elemental_dps()
        .insert_metadata()
        .insert_currency_info()
        .insert_item_base_info()
        .insert_sub_mod_values()
        .insert_skills()
        .remove_local_mods()
        .clean_columns()
        .data
    )
