import pprint
from datetime import datetime
import random

from src.market_item_analysis.shared.io_manager import IoManager
from src.market_item_analysis.trade_api import TradeApiHandler
from src.market_item_analysis.trade_api.api_response_obj import ApiResponse
from src.market_item_analysis.trade_api.query import QueryPresets


class _IntakeGatekepeer:

    def __init__(self,
                 existing_responses: list[ApiResponse],
                 hours_since_pulled_threshold: int):
        sorted_responses = sorted(existing_responses, key=lambda r: r.date_fetched)
        self._date_fetched_d = {r: r.date_fetched for r in sorted_responses}
        self._hours_since_pulled_threshold = hours_since_pulled_threshold

    def should_process_api_response(self, response: ApiResponse) -> bool:
        if response not in self._date_fetched_d:
            self._date_fetched_d[response] = response.date_fetched
            return True

        hours_since_pulled = (response.date_fetched - self._date_fetched_d[response]).total_seconds() / 3600
        return hours_since_pulled >= self._hours_since_pulled_threshold

    def add_responses(self, responses: list[ApiResponse]):
        self._date_fetched_d.update({r: r.date_fetched for r in responses})

class RawListingLoader:

    def __init__(self,
                 trade_api_handler: TradeApiHandler,
                 io_manager: IoManager):
        self.trade_api_handler = trade_api_handler
        self._io_manager = io_manager

        existing_responses = [ApiResponse(r) for r in io_manager.load_raw_responses()]
        self._intake_gatekeeper = _IntakeGatekepeer(existing_responses=existing_responses,
                                                    hours_since_pulled_threshold=3)

        self._raw_responses_pulled = 0
        self._valid_responses_pulled = 0

    def _clean_raw_response(self, d: dict) -> dict:
        cleaned = {}
        for k, v in d.items():
            if k in {'hideout_token', 'icon'}:
                continue
            if isinstance(v, dict):
                cleaned[k] = self._clean_raw_response(v)
            else:
                cleaned[k] = v
        return cleaned

    def pull_from_trade_api(self, pull_minutes_limit: int):
        pull_start_time = datetime.now()
        training_queries = QueryPresets.create_training_data_queries()
        random.shuffle(training_queries)

        for i, raw_responses in enumerate(self.trade_api_handler.fetch_responses(training_queries)):
            raw_responses = [self._clean_raw_response(r) for r in raw_responses]

            self._raw_responses_pulled += len(raw_responses)

            responses = [ApiResponse(r) for r in raw_responses]

            valid_responses = [r for r in responses
                               if self._intake_gatekeeper.should_process_api_response(r)]
            self._intake_gatekeeper.add_responses(valid_responses)

            self._valid_responses_pulled += len(valid_responses)

            self._io_manager.save_raw_responses([r.raw_response_data for r in valid_responses])

            print(f"\nPulled from Trade API:"
                  f"\nIteration {i}:"
                  f"\n\tAPI responses: {len(raw_responses)}"
                  f"\n\tValid responses: {len(valid_responses)}"
                  f"\nTotal:"
                  f"\n\tAPI responses: {self._raw_responses_pulled}"
                  f"\n\tValid listings created: {self._valid_responses_pulled}")

            current_time = datetime.now()
            runtime_minutes = (current_time - pull_start_time).total_seconds() / 60.0

            if runtime_minutes >= pull_minutes_limit:
                return
