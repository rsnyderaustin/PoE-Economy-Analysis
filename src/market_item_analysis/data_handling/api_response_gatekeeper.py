from src.market_item_analysis.instances_and_definitions.item_instances import EquipmentListing
from src.market_item_analysis.trade_api.api_response_obj import ApiResponse


class ApiResponseGatekeeper:

    def __init__(self, existing_listings: list[EquipmentListing] = None):
        self._date_fetched_d = dict()
        if existing_listings:
            sorted_listings = sorted(existing_listings, key=lambda l: l.metadata.date_fetched)
            self._date_fetched_d = {l.metadata.listing_id: l.metadata.date_fetched for l in sorted_listings}
        
    def should_process_api_response(self, 
                                    api_response: ApiResponse,
                                    hours_since_last_threshold: int = 3) -> bool:
        id_ = api_response.listing_id
        d_f = api_response.date_fetched
        if id_ not in self._date_fetched_d:
            self._date_fetched_d[id_] = d_f
            return True

        hours_since = (d_f - self._date_fetched_d[id_]).total_seconds() / 3600
        return hours_since >= hours_since_last_threshold

    def add_listings(self, listings: list[EquipmentListing]):
        for l in listings:
            id_ = l.metadata.listing_id
            d_f = l.metadata.date_fetched

            if id_ not in self._date_fetched_d:
                self._date_fetched_d[id_] = d_f
                continue

            self._date_fetched_d[id_] = max(d_f, self._date_fetched_d[id_])
        
        