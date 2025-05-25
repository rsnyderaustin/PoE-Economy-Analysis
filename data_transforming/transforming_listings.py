import logging
import pprint
from datetime import datetime
from abc import ABC, abstractmethod
from collections.abc import Iterable

import pandas as pd

from instances_and_definitions import ModifiableListing
from shared import shared_utils, item_enums, ItemCategoryGroups
from shared.item_enums import LocalMod, DerivedMod, ItemCategory


class ListingFeatureCalculator(ABC):
    applicable_item_categories = []
    input_columns = set()

    @classmethod
    @abstractmethod
    def calculate(cls, listing: ModifiableListing) -> dict:
        pass

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, 'input_columns'):
            raise TypeError(f"{cls.__name__} must define 'input_columns'.")
        if not hasattr(cls, 'applicable_item_categories'):
            raise TypeError(f"{cls.__name__} must define 'applicable_item_categories'.")


class CalculatorRegistry:
    _calculators = dict()

    @classmethod
    def register(cls, calculator: type[ListingFeatureCalculator]):
        for cat in calculator.applicable_item_categories:
            if cat not in cls._calculators:
                cls._calculators[cat] = list()

            cls._calculators[cat].append(calculator)

        return calculator

    @classmethod
    def fetch_calculators(cls, item_category: ItemCategory) -> list[ListingFeatureCalculator]:
        return cls._calculators[item_category] if item_category in cls._calculators else []


@CalculatorRegistry.register
class MaxQualityPdpsCalculator(ListingFeatureCalculator):
    applicable_item_categories = ItemCategoryGroups.fetch_martial_weapon_categories()
    input_columns = {LocalMod.QUALITY, LocalMod.PHYSICAL_DAMAGE, LocalMod.ATTACKS_PER_SECOND}

    @classmethod
    def calculate(cls, listing: ModifiableListing):
        if listing.item_category not in cls.applicable_item_categories:
            raise TypeError(f"Listing with item category {listing.item_category} called {cls.__name__}")

        current_multiplier = 1 + (listing.quality / 100)
        max_multiplier = 1.20

        # Calculate the base damage and then the 20% quality damage
        phys_damage = getattr(listing, LocalMod.PHYSICAL_DAMAGE.value, 0)
        base_damage = phys_damage / current_multiplier
        max_quality_damage = base_damage * max_multiplier

        attack_speed = getattr(listing, LocalMod.ATTACKS_PER_SECOND.value, 0)
        max_quality_pdps = max_quality_damage * attack_speed

        return {DerivedMod.MAX_QUALITY_PDPS: max_quality_pdps}


@CalculatorRegistry.register
class ElementalDpsCalculator(ListingFeatureCalculator):
    applicable_item_categories = ItemCategoryGroups.fetch_martial_weapon_categories()
    input_columns = {LocalMod.COLD_DAMAGE, LocalMod.FIRE_DAMAGE, LocalMod.LIGHTNING_DAMAGE,
                     LocalMod.ATTACKS_PER_SECOND}

    @classmethod
    def calculate(cls, listing: ModifiableListing):
        if listing.item_category not in cls.applicable_item_categories:
            raise TypeError(f"Listing with item category {listing.item_category} called {cls.__name__}")

        cold_damage = getattr(listing, LocalMod.COLD_DAMAGE.value, 0)
        fire_damage = getattr(listing, LocalMod.FIRE_DAMAGE.value, 0)
        lightning_damage = getattr(listing, LocalMod.LIGHTNING_DAMAGE.value, 0)
        attacks_per_second = getattr(listing, LocalMod.ATTACKS_PER_SECOND.value, 0)

        return {
            DerivedMod.COLD_DPS: cold_damage * attacks_per_second,
            DerivedMod.FIRE_DPS: fire_damage * attacks_per_second,
            DerivedMod.LIGHTNING_DPS: lightning_damage * attacks_per_second,
            DerivedMod.ELEMENTAL_DPS: (cold_damage + fire_damage + lightning_damage) * attacks_per_second
        }


class ListingsTransforming:
    _select_col_types = {
        'atype': 'category',
        'btype': 'category',
        'rarity': 'category',
        'identified': bool,
        'corrupted': bool
    }

    @staticmethod
    def to_flat_rows(listings: list[ModifiableListing]) -> dict:
        """

        :param listings:
        :return: Listings flattened into rows - used for database storage
        """
        compiled_data = dict()
        for row, listing in enumerate(listings):
            flattened_data = (
                _PricePredictTransformer(listing)
                .insert_listing_properties()
                .apply_calculators(delete_input_columns=True)
                .insert_metadata()
                .insert_currency_info()
                .insert_item_base_info()
                .insert_sub_mod_values()
                .insert_skills()
                .clean_columns()
                .flattened_data
            )

            # Fill in the previously missing columns with Nones up to all the rows before this loop
            cols_missing_from_compiled = [col for col in flattened_data if col not in compiled_data]
            compiled_data.update(
                {
                    missing_col: [] if row == 0 else [None] * row
                    for missing_col in cols_missing_from_compiled
                }
            )

            # Append None to any existing column that was not in this listing
            cols_missing_from_listing = [col for col in compiled_data if col not in flattened_data]
            for col in cols_missing_from_listing:
                compiled_data[col].append(None)

            for k, v in flattened_data.items():
                compiled_data[k].append(v)

        return compiled_data

    @classmethod
    def to_price_predict_df(cls, listings: list[ModifiableListing] = None, rows: dict = None) -> pd.DataFrame:
        """

        :param listings:
        :param rows:
        :return: Listings or rows data formatted into a DataFrame for the Price Predict AI model
        """
        if not rows:
            rows = cls.to_flat_rows(listings)

        df = pd.DataFrame(rows)

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


class _PricePredictTransformer:

    def __init__(self, listing: ModifiableListing):
        self.listing = listing
        self.flattened_data = dict()

        self.calculator_registry = CalculatorRegistry()

        # Derived columns like pdps/edps shouldn't be compared to their source columns in analyses like stats.
        self.derived_columns = dict()

    def _determine_date_fetched(self):
        return datetime.strptime(self.listing.date_fetched, "%Y-%m-%dT%H:%M:%SZ")

    def insert_listing_properties(self):
        flattened_properties = dict()
        for property_name, property_value in self.listing.item_properties.items():
            if isinstance(property_value, Iterable):
                flattened_properties[property_name] = 0
                for v in property_value:
                    if isinstance(v, int) or isinstance(v, float):
                        flattened_properties[property_name] += v
                    elif len(v) == 2:
                        flattened_properties[property_name] += ((v[0] + v[1]) / 2)
                    elif len(v) == 1:
                        flattened_properties[property_name] += v[0]
                    else:
                        raise ValueError(f"Property value {property_value} has unexpected structure.")
            else:
                flattened_properties[property_name] = property_value

        self.flattened_data.update(flattened_properties)
        return self

    def apply_calculators(self, delete_input_columns=True):
        calculators = self.calculator_registry.fetch_calculators(self.listing.item_category)
        derived_col_values = {
            col_e.value: val
            for calc in calculators
            for col_e, val in calc.calculate(self.listing).items()
        }
        self.flattened_data.update(derived_col_values)

        if delete_input_columns:
            input_cols = set(col for calc in calculators for col in calc.input_columns)
            for col_e in input_cols:
                self.flattened_data.pop(col_e.value, None)

        return self

    def insert_metadata(self):
        metadata = {
            'date_fetched': self._determine_date_fetched(),
            'minutes_since_listed': self.listing.minutes_since_listed,
            'minutes_since_league_start': self.listing.minutes_since_league_start
        }
        self.flattened_data.update(metadata)
        return self

    def insert_currency_info(self):
        self.flattened_data['currency'] = self.listing.currency
        self.flattened_data['currency_amount'] = self.listing.currency_amount

        exalts_price = shared_utils.CurrencyConverter().convert_to_exalts(
            currency=self.listing.currency,
            currency_amount=self.listing.currency_amount,
            relevant_date=self._determine_date_fetched()
        )
        self.flattened_data['exalts'] = exalts_price
        return self

    def insert_item_base_info(self):
        self.flattened_data['open_prefixes'] = self.listing.open_prefixes
        self.flattened_data['open_suffixes'] = self.listing.open_suffixes
        self.flattened_data['atype'] = self.listing.item_atype
        self.flattened_data['ilvl'] = self.listing.ilvl
        self.flattened_data['category'] = self.listing.item_category.value
        self.flattened_data['rarity'] = self.listing.rarity
        self.flattened_data['corrupted'] = self.listing.corrupted
        self.flattened_data['identified'] = self.listing.identified
        return self

    def insert_sub_mod_values(self):
        sub_mods = [sub_mod for mod in self.listing.mods for sub_mod in mod._sub_mods]

        summed_sub_mods = {}
        for sub_mod in sub_mods:
            if sub_mod.actual_values:
                avg_value = sum(sub_mod.actual_values) / len(sub_mod.actual_values)
                if sub_mod.mod_id not in summed_sub_mods:
                    summed_sub_mods[sub_mod.sanitized_mod_text] = avg_value
                else:
                    summed_sub_mods[sub_mod.sanitized_mod_text] += avg_value
            else:
                # If there is no value then it's just a static property (ex: "You cannot be poisoned"), and so
                # we assign it a 1 to indicate to the model that it's an active mod
                summed_sub_mods[sub_mod.sanitized_mod_text] = 1

        self.flattened_data.update(summed_sub_mods)
        return self

    def insert_skills(self):
        skills_dict = {item_skill.name: item_skill.level for item_skill in self.listing.item_skills}
        skills_dict = {skill_name: lvl for skill_name, lvl in skills_dict.items()}
        self.flattened_data.update(skills_dict)
        return self

    def clean_columns(self):
        # Some columns have just one letter - not sure why but need to find out
        cols_to_remove = [col for col in self.flattened_data if len(col) == 1]
        for col in cols_to_remove:
            logging.error(f"Found 1-length attribute name {cols_to_remove} for listing: "
                          f"\n{pprint.pprint(self.listing.__dict__)}")
            self.flattened_data.pop(col)
        return self
