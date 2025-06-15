from datetime import date

import pandas as pd

from shared.enums.trade_enums import Currency


class CurrencyConverter:
    _instance = None
    _initialized = None

    def __new__(cls, conversions_df: pd.DataFrame):
        if cls._instance is None:
            cls._instance = super(CurrencyConverter, cls).__new__(cls)
        return cls._instance

    def __init__(self, conversions_df: pd.DataFrame):

        if self._initialized:
            return
        self._initialized = True

        self.conversions_dict = self._create_conversions_dict(conversions_df)

        self._conversion_cache = {}

    @staticmethod
    def _create_conversions_dict(conversions_df: pd.DataFrame) -> dict:
        df = conversions_df
        df['date'] = pd.to_datetime(df['date'])

        # Create a full date range covering all currencies
        full_date_range = pd.date_range(df['date'].min(), df['date'].max(), freq='D')

        # Group by currency and interpolate each group
        conversion_dict = {}
        for currency, group in df.groupby('currency'):
            group = group.set_index('date').sort_index()
            group = group.reindex(full_date_range)
            group['div_per_currency'] = group['div_per_currency'].interpolate(method='linear')
            group.index.name = 'date'
            # Convert to dictionary with datetime.date keys
            conversion_dict[currency] = {
                date.date(): rate for date, rate in group['div_per_currency'].items()
            }

        return conversion_dict

    def convert_to_divs(self, currency: Currency, currency_amount: int | float, relevant_date: date):
        if currency == Currency.DIVINE_ORB:
            return currency_amount

        simple_date = (relevant_date.year, relevant_date.month, relevant_date.day)
        convert_key = (currency, currency_amount, simple_date)
        if convert_key in self._conversion_cache:
            return self._conversion_cache[convert_key]

        closest_date = min(self.conversions_dict.keys(), key=lambda d: abs(d - relevant_date))

        exchange_rate = self.conversions_dict[closest_date][currency.value]
        converted_amount = currency_amount * exchange_rate

        self._conversion_cache[convert_key] = converted_amount

        return converted_amount
