from enum import Enum


class ListingColumn(Enum):
    PRICE_CURRENCY = "price_currency"
    PRICE_AMOUNT = 'price_amount'
    DAYS_SINCE_LEAGUE_START = 'days_since_league_start'
    PRICE = 'listing_price'
    LOG_PRICE = 'log_listing_price'
    EQUIPMENT_CATEGORY = 'equipment_category'


