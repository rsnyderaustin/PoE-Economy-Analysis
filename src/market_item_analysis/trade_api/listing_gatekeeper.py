from datetime import datetime

from src.market_item_analysis.instances_and_definitions import EquipmentListing
from src.market_item_analysis.psql import PostgreSqlManager
from src.market_item_analysis.shared import utils


class ListingImportGatekeeper:

    def __init__(self, existing_listings: list[EquipmentListing]):
        self._d = dict()
        for l in existing_listings:
            date_fetched = l.metadata.date_fetched
            if l not in self._d:
                self._d[l] = date_fetched
                continue

            if self._d[l] < date_fetched:
                self._d[l] = date_fetched

    def should_process_listing(self, listing: EquipmentListing) -> bool:
        if listing not in self._d:
            self._d[listing] = listing.metadata.date_fetched
            return True

        minutes_since_last_fetch = (listing.metadata.date_fetched - self._d[listing]).total_seconds() / 60

        self._d[listing] = listing.metadata.date_fetched

        return minutes_since_last_fetch > 180
