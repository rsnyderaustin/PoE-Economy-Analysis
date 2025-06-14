import logging
import pprint
from abc import ABC, abstractmethod
from collections.abc import Iterable

import core
from core import CurrencyConverter
from instances_and_definitions import ModifiableListing
from program_logging import LogsHandler, LogFile, log_errors
from shared import shared_utils
from shared.enums import ItemEnumGroups, WhichCategoryType
from shared.enums.item_enums import AType, LocalMod, CalculatedMod
from shared.enums.trade_enums import Currency

lh = LogsHandler()
parse_log = lh.fetch_log(LogFile.API_PARSING)
price_predict_log = lh.fetch_log(LogFile.PRICE_PREDICT_MODEL)
i_o_log = lh.fetch_log(LogFile.INPUT_OUTPUT)


class ListingFeatureCalculator(ABC):
    applicable_atypes = []
    input_columns = set()
    calculated_columns = set()

    @classmethod
    @abstractmethod
    def calculate(cls, listing: ModifiableListing) -> dict:
        pass

    @log_errors(logging.getLogger())
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, 'input_columns'):
            raise TypeError(f"{cls.__name__} must define 'input_columns'.")
        if not hasattr(cls, 'calculated_columns'):
            raise TypeError(f"{cls.__name__} must define 'calculated_columns'.")
        if not hasattr(cls, 'applicable_atypes'):
            raise TypeError(f"{cls.__name__} must define 'applicable_item_categories'.")

    def __hash__(self):
        return hash(str(self.__class__))


class CalculatorRegistry:
    _item_atype_to_calculators = dict()

    @classmethod
    def register(cls, calculator: type[ListingFeatureCalculator]):
        for atype in calculator.applicable_atypes:
            if atype not in cls._item_atype_to_calculators:
                cls._item_atype_to_calculators[atype] = list()

            cls._item_atype_to_calculators[atype].append(calculator)

        return calculator

    @classmethod
    def fetch_calculators(cls, item_atype: AType) -> list[ListingFeatureCalculator]:
        return cls._item_atype_to_calculators[item_atype] if item_atype in cls._item_atype_to_calculators else []

    @classmethod
    def input_columns(cls) -> set[str]:
        calcs = {calc for item_category, calcs in cls._item_atype_to_calculators.items() for calc in calcs}
        return {input_col for calc in calcs for input_col in calc.input_columns}

    @classmethod
    def calculated_columns(cls) -> list[str]:
        calcs = [calc for item_category, calcs in cls._item_atype_to_calculators.items() for calc in calcs]
        return [calc_col for calc in calcs for calc_col in calc.calculated_columns]


@CalculatorRegistry.register
class MaxQualityPdpsCalculator(ListingFeatureCalculator):
    applicable_atypes = ItemEnumGroups.fetch_martial_weapons(which=WhichCategoryType.ATYPE)
    input_columns = {LocalMod.QUALITY, LocalMod.PHYSICAL_DAMAGE, LocalMod.ATTACKS_PER_SECOND}
    calculated_columns = {CalculatedMod.MAX_QUALITY_PDPS.value}

    @classmethod
    def calculate(cls, listing: ModifiableListing):
        if listing.item_atype not in cls.applicable_atypes:
            msg = f"Listing with item category {listing.item_atype} called {cls.__name__}"
            logging.error(msg)
            raise TypeError(msg)

        current_multiplier = 1 + (listing.quality / 100)
        max_multiplier = 1 + (listing.max_quality / 100)

        # Calculate the base damage and then the 20% quality damage
        phys_damage = listing.item_properties.get(LocalMod.PHYSICAL_DAMAGE.value, 0)
        base_damage = phys_damage / current_multiplier
        max_quality_damage = base_damage * max_multiplier

        attack_speed = listing.item_properties.get(LocalMod.ATTACKS_PER_SECOND.value, 0)
        max_quality_pdps = max_quality_damage * attack_speed

        i_o_log.info(
            f"Phys damage {phys_damage} & quality {listing.quality} = Max quality phys damage {max_quality_damage}"
            f"\n-> Max quality phys damage {max_quality_damage} * attacks per second {attack_speed} "
            f"= Max quality Pdps {max_quality_pdps}"
        )

        return {CalculatedMod.MAX_QUALITY_PDPS: max_quality_pdps}


@CalculatorRegistry.register
class NonPhysicalDpsCalculator(ListingFeatureCalculator):
    applicable_atypes = ItemEnumGroups.fetch_martial_weapons(which=WhichCategoryType.ATYPE)
    input_columns = {LocalMod.CHAOS_DAMAGE, LocalMod.COLD_DAMAGE, LocalMod.FIRE_DAMAGE, LocalMod.LIGHTNING_DAMAGE,
                     LocalMod.ATTACKS_PER_SECOND}
    calculated_columns = {CalculatedMod.COLD_DPS.value,
                          CalculatedMod.FIRE_DPS.value,
                          CalculatedMod.LIGHTNING_DPS.value,
                          CalculatedMod.CHAOS_DPS.value,
                          CalculatedMod.ELEMENTAL_DPS.value}

    @classmethod
    @log_errors(parse_log)
    def calculate(cls, listing: ModifiableListing):
        if listing.item_atype not in cls.applicable_atypes:
            raise TypeError(f"Listing with item category {listing.item_atype} called {cls.__name__}")

        cold_damage = listing.item_properties.get(LocalMod.COLD_DAMAGE.value, 0)
        fire_damage = listing.item_properties.get(LocalMod.FIRE_DAMAGE.value, 0)
        lightning_damage = listing.item_properties.get(LocalMod.LIGHTNING_DAMAGE.value, 0)
        chaos_damage = listing.item_properties.get(LocalMod.CHAOS_DAMAGE.value, 0)
        attacks_per_second = listing.item_properties.get(LocalMod.ATTACKS_PER_SECOND.value, 0)

        cold_dps = cold_damage * attacks_per_second
        fire_dps = fire_damage * attacks_per_second
        lightning_dps = lightning_damage * attacks_per_second
        chaos_dps = chaos_damage * attacks_per_second
        elemental_dps = (cold_damage + fire_damage + lightning_damage) * attacks_per_second

        i_o_log.info(f"Cold damage ({cold_damage}) * attack speed ({attacks_per_second}) = Cold DPS ({cold_dps})")
        i_o_log.info(f"Fire damage ({fire_damage}) * attack speed ({attacks_per_second}) = Fire DPS ({fire_dps})")
        i_o_log.info(f"Lightning damage ({lightning_damage}) * attack speed ({attacks_per_second}) "
                     f"= Lightning DPS ({lightning_dps})")
        i_o_log.info(f"Chaos damage ({chaos_damage}) * attack speed ({attacks_per_second}) = Chaos DPS ({chaos_dps})")
        i_o_log.info(f"Elemental DPS = (cold ({cold_damage}) + fire ({fire_damage}) + lightning ({lightning_damage})) "
                     f"* attack speed ({attacks_per_second}) = ({elemental_dps})")

        return {
            CalculatedMod.COLD_DPS: cold_dps,
            CalculatedMod.FIRE_DPS: fire_dps,
            CalculatedMod.LIGHTNING_DPS: lightning_dps,
            CalculatedMod.CHAOS_DPS: chaos_dps,
            CalculatedMod.ELEMENTAL_DPS: elemental_dps,
        }


class ListingsTransforming:
    _select_col_types = {
        'atype': 'category',
        'btype': 'category',
        'rarity': 'category',
        'identified': bool,
        'corrupted': bool
    }

    # PricePredictDf naturally only includes mod columns. So we have to explicitly include other columns to feed into
    # the model
    _price_predict_specific_cols = {
        'minutes_since_league_start',
        'atype',
        'divs',
        *CalculatorRegistry.calculated_columns()
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
            parse_log.info(
                f"--- Listing ---\n{pprint.pformat(listing)}\n-> Flattened into ->\n{pprint.pformat(flattened_data)}"
            )

            # Fill in the previously missing columns with Nones up to all the rows before this loop
            cols_missing_from_compiled = [col for col in flattened_data if col not in compiled_data]
            compiled_data.update(
                {
                    missing_col: [] if row == 0 else [None] * row
                    for missing_col in cols_missing_from_compiled
                }
            )

            # Append None to any existing column that was not in this specific listing
            cols_missing_from_listing = [col for col in compiled_data if col not in flattened_data]
            for col in cols_missing_from_listing:
                compiled_data[col].append(None)

            for k, v in flattened_data.items():
                compiled_data[k].append(v)

            parse_log.info(f"Flattened data being inserted into PSQL:\n{pprint.pformat(flattened_data)}")

        return compiled_data

    @classmethod
    def _determine_valid_price_predict_columns(cls, df) -> list[str]:
        mod_cols = [col for col in df.columns if col.startswith('mod_')]
        valid_cols = [*cls._price_predict_specific_cols, *mod_cols]
        return valid_cols

    @classmethod
    def _apply_determine_divs_price(cls, row):
        return CurrencyConverter().convert_to_divs(
            currency=Currency(row['currency']),
            currency_amount=row['currency_amount'],
            relevant_date=shared_utils.format_date_into_utc(row['date_fetched'])
        )

    @staticmethod
    @log_errors(price_predict_log)
    def _fill_out_features_columns(features_df: 'pd.DataFrame', model_features):
        cols_missing_from_model = [col for col in features_df.columns if col not in model_features]
        if cols_missing_from_model:
            raise ValueError(f"Columns {cols_missing_from_model} in this listing but not in model. Model training data is "
                             f"therefore incomplete.")

        # Ensure all model-required columns exist in features
        cols_missing_from_listing = [col for col in model_features if col not in features_df.columns]
        for col in cols_missing_from_listing:
            features_df[col] = None  # fill in with 0 indicating the mod is not present

    @classmethod
    def to_price_predict_df(cls,
                            listings: list[ModifiableListing] = None,
                            rows: dict[str: list] = None,
                            existing_model=None) -> 'pd.DataFrame':
        """

        :param listings: Listings to format into a DataFrame for the PricePredict model.
        :param rows: Rows must be provided if listings are not. Expected format: {column name : column values}
        :param existing_model: If using this method to predict from an existing PricePredict model, that model should be provided
            here. The model is used in this function to format the columns so that you can just feed the DataFrame output straight into the model.
        :return: Data formatted into a DataFrame for the PricePredict model
        """

        import pandas as pd

        if not rows:
            rows = cls.to_flat_rows(listings)

        df = pd.DataFrame(rows)
        df = df.drop_duplicates()

        df['divs'] = df.apply(cls._apply_determine_divs_price, axis=1)

        cols = cls._determine_valid_price_predict_columns(df)

        price_predict_log.info(f"Columns removed from PricePredict DataFrame:\n"
                               f"{[col for col in df.columns if col not in cols]}")

        df = df[cols]

        for col, dtype in cls._select_col_types.items():
            if col in df.columns:
                df[col] = df[col].astype(dtype)

        df = df.select_dtypes(include=['int64', 'float64', 'bool', 'category'])

        if existing_model:
            features_df = df.drop(columns=['divs'])
            cls._fill_out_features_columns(features_df=features_df,
                                           model_features=existing_model.features)
            df = pd.concat([features_df, df['divs']])

        return df


class _PricePredictTransformer:
    _non_mod_cols = {'minutes_since_league_start', 'atype'}

    def __init__(self, listing: ModifiableListing):
        self.listing = listing
        parse_log.info(f"NEW LISTING DATA\n{pprint.pformat(listing)}")

        self.flattened_data = dict()

        self.calculator_registry = CalculatorRegistry()

        # Derived columns like pdps/edps shouldn't be compared to their source columns in analyses like stats.
        self.derived_columns = dict()

    @log_errors(parse_log)
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
        calculators = self.calculator_registry.fetch_calculators(self.listing.item_atype)
        derived_col_values = {
            col_e.value: val
            for calc in calculators
            for col_e, val in calc.calculate(self.listing).items()
        }
        parse_log.info(f"Listing calculations:\n{pprint.pformat(derived_col_values)}\n")
        self.flattened_data.update(derived_col_values)

        if delete_input_columns:
            input_cols = set(col for calc in calculators for col in calc.input_columns)
            for col_e in input_cols:
                self.flattened_data.pop(col_e.value, None)

        return self

    def insert_metadata(self):
        metadata = {
            'my_id': self.listing.my_id,
            'listing_id': self.listing.listing_id,
            'date_fetched': self.listing.date_fetched,
            'minutes_since_listed': self.listing.minutes_since_listed,
            'minutes_since_league_start': self.listing.minutes_since_league_start
        }
        self.flattened_data.update(metadata)
        return self

    def insert_currency_info(self):
        self.flattened_data['currency'] = self.listing.currency.value
        self.flattened_data['currency_amount'] = self.listing.currency_amount

        return self

    def insert_item_base_info(self):
        self.flattened_data['open_prefixes'] = self.listing.open_prefixes
        self.flattened_data['open_suffixes'] = self.listing.open_suffixes
        self.flattened_data['atype'] = self.listing.item_atype.value
        self.flattened_data['ilvl'] = self.listing.ilvl
        self.flattened_data['rarity'] = self.listing.rarity.value
        self.flattened_data['corrupted'] = self.listing.corrupted
        self.flattened_data['identified'] = self.listing.identified
        return self

    def insert_sub_mod_values(self):
        sub_mods = [sub_mod for mod in self.listing.mods for sub_mod in mod.sub_mods]

        summed_sub_mods = {}
        for sub_mod in sub_mods:
            # We add the 'mod_' prefix here so that we can identify which columns are mod columns in the future
            mod_text = f"mod_{sub_mod.sanitized_text}"
            if sub_mod.actual_values:
                avg_value = sum(sub_mod.actual_values) / len(sub_mod.actual_values)
                if sub_mod.sub_mod_hash not in summed_sub_mods:
                    summed_sub_mods[mod_text] = avg_value
                else:
                    summed_sub_mods[mod_text] += avg_value
            else:
                # If there is no value then it's just a static property (ex: "You cannot be poisoned"), and so
                # we assign it a 1 to indicate to the model that it's an active mod
                summed_sub_mods[mod_text] = 1

        parse_log.info(f"Summed sub-mods:\n{pprint.pformat(summed_sub_mods)}\n")
        self.flattened_data.update(summed_sub_mods)
        return self

    def insert_skills(self):
        skills_dict = {item_skill.name: item_skill.level for item_skill in self.listing.item_skills}
        skills_dict = {skill_name: lvl for skill_name, lvl in skills_dict.items()}
        parse_log.info(f"Skills:\n{pprint.pformat(skills_dict)}")
        self.flattened_data.update(skills_dict)
        return self

    def clean_columns(self):
        for col, value in self.flattened_data.items():
            if isinstance(value, float):
                self.flattened_data[col] = round(value, 5)

        # Some columns have just one letter - not sure why but need to find out
        cols_to_remove = [col for col in self.flattened_data if len(col) == 1]
        for col in cols_to_remove:
            parse_log.error(f"Found 1-length attribute name {cols_to_remove} for listing: "
                            f"\n{pprint.pformat(self.flattened_data)}\nRemoving the extra column")
            self.flattened_data.pop(col)

        return self
