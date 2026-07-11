from datetime import datetime
import random

from src.market_item_analysis.core.input_output import IoManager
from src.market_item_analysis.trade_api import TradeApiInterface
from src.market_item_analysis.trade_api.query.objects import TradeApiQuery, TradeApiQueryPlan
from src.market_item_analysis.trade_api.requesting.fetching import TradeApiResultsResponse
from src.market_item_analysis.trade_api.trade_result import ApiResponse, TradeApiResult
from src.market_item_analysis.trade_api.query import QueryPresets


class TradeApiResponseMetrics:

    def __init__(self):
        self.results = 0
        self.valid_results = 0


class TradeApiResultValidator:

    def __init__(self):
        self._result_ids = set()

    def add_listings(self, results: list[TradeApiResult]):
        self._result_ids.update({result.__hash__() for result in results})

    def is_valid(self, result: TradeApiResult) -> bool:
        return result.__hash__() not in self._result_ids


class TradeApiResultsIngestor:

    def __init__(self):
        self._validator = TradeApiResultValidator()
        self.metrics = TradeApiResponseMetrics()

    def ingest(self, query_plans: list[TradeApiQueryPlan], pull_minutes_limit: int):
        pull_start_time = datetime.now()

        random.shuffle(query_plans)

        for query_plan in query_plans:
            for i, trade_api_response in enumerate(TradeApiInterface.fetch_responses(query_plan=query_plan)):
                self.metrics.results += len(trade_api_response.results)

                valid_results = [result for result in trade_api_response.results if self._validator.is_valid(result)]
                self.metrics.valid_results += len(valid_results)


        for i, trade_api_response in enumerate(TradeApiInterface.fetch_responses()):
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
                print("Reached pull time limit. Returning...")
                return


class _IntakeGatekepeer:

    def __init__(self,
                 existing_responses: list[ApiResponse],
                 hours_since_pulled_threshold: int):
        sorted_responses = sorted(existing_responses, key=lambda r: r.date_fetched)
        self._date_fetched_d = {r: r.date_fetched for r in sorted_responses}
        self._hours_since_pulled_threshold = hours_since_pulled_threshold

    def should_process_api_response(self, response: TradeApiResultsResponse) -> bool:
        if response not in self._date_fetched_d:
            self._date_fetched_d[response] = response.date_fetched
            return True

        hours_since_pulled = (response.date_fetched - self._date_fetched_d[response]).total_seconds() / 3600
        return hours_since_pulled >= self._hours_since_pulled_threshold

    def add_responses(self, responses: list[ApiResponse]):
        self._date_fetched_d.update({r: r.date_fetched for r in responses})

class RawListingLoader:

    def __init__(self,
                 trade_api_handler: TradeApiInterface,
                 io_manager: IoManager):
        self.trade_api_handler = trade_api_handler
        self._io_manager = io_manager

        existing_responses = [ApiResponse(r) for r in io_manager.load_raw_responses()]
        self._intake_gatekeeper = _IntakeGatekepeer(existing_responses=existing_responses,
                                                    hours_since_pulled_threshold=3)

        self._raw_responses_pulled = 0
        self._valid_responses_pulled = 0

