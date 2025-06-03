from datetime import datetime

from psql import PostgreSqlManager


class ListingImportGatekeeper:

    def __init__(self, psql_manager: PostgreSqlManager):
        if psql_manager.skip_sql:
            self.id_fetch_dates = dict()
            return

        dates_and_ids = psql_manager.fetch_columns_data(table_name='listings',
                                                        columns=['date_fetched', 'listing_id'])
        self.id_fetch_dates = dict()
        for date, listing_id in dates_and_ids:
            if listing_id not in self.id_fetch_dates:
                self.id_fetch_dates[listing_id] = date
            else:
                if date > self.id_fetch_dates[listing_id]:
                    self.id_fetch_dates[listing_id] = date

    def listing_is_valid(self, listing_id: str, date_fetched: datetime) -> bool:
        if listing_id not in self.id_fetch_dates:
            self.id_fetch_dates[listing_id] = date_fetched
            return True

        latest_fetch_date = self.id_fetch_dates[listing_id]
        minutes_since_last_fetch = (date_fetched - latest_fetch_date).total_seconds() / 60

        self.id_fetch_dates[listing_id] = date_fetched
        return minutes_since_last_fetch > 180
