from datetime import datetime

from psql import PostgreSqlManager


class ListingImportGatekeeper:

    def __init__(self, psql_manager: PostgreSqlManager):
        if psql_manager.skip_sql:
            self.keys = set()
            return

        dates_and_ids = psql_manager.fetch_columns_data(table_name='listings',
                                                        columns=['date_fetched', 'listing_id'])
        self.keys = {
            (listing_id, date_fetched)
            for listing_id, date_fetched in zip(dates_and_ids['listing_id'], dates_and_ids['date_fetched'])
        }

    def listing_is_valid(self, listing_id: str, date_fetched: datetime, register_if_valid=True) -> bool:
        is_valid = (listing_id, date_fetched) not in self.keys
        if not is_valid:
            return False

        if register_if_valid:
            self.register_listing(listing_id=listing_id, date_fetched=date_fetched)

        return True

    def register_listing(self, listing_id: str, date_fetched: datetime):
        self.keys.add((listing_id, date_fetched))
