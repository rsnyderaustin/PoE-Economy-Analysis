from datetime import datetime
import random
from typing import Generator

from src.market_item_analysis.trade_api import TradeApiInterface
from src.market_item_analysis.trade_api.query.objects import TradeApiQueryPlan
from src.market_item_analysis.trade_api.raw_result import TradeApiResult


class TradeApiResponseMetrics:

    def __init__(self):
        self.results = 0
        self.valid_results = 0


class TradeApiResultValidator:

    def __init__(self, existing_results: list[TradeApiResult]):
        self._result_ids = {r.__hash__() for r in existing_results}

    def add_listings(self, results: list[TradeApiResult]):
        self._result_ids.update({result.__hash__() for result in results})

    def is_valid(self,
                 result: TradeApiResult,
                 add_valid_listing: bool = True) -> bool:
        if result.__hash__() not in self._result_ids:
            if add_valid_listing:
                self._result_ids.add(result.__hash__())
            return True
        return False


class PullTimeMonitor:

    def __init__(self, pull_minutes_limit: int):
        self._pull_seconds_limit = pull_minutes_limit * 60
        self._pull_start_time = datetime.now()

    def over_time(self) -> bool:
        current_time = datetime.now()
        seconds_elapsed = current_time - self._pull_start_time
        return seconds_elapsed.total_seconds() > self._pull_seconds_limit

class TradeApiResultsIngestor:

    def __init__(self, validator: TradeApiResultValidator):
        self._validator = validator
        self.metrics = TradeApiResponseMetrics()

    def ingest(self, query_plans: list[TradeApiQueryPlan], pull_minutes_limit: int) -> Generator[list[TradeApiResult], None, None]:
        pull_time_monitor = PullTimeMonitor(pull_minutes_limit)

        while not pull_time_monitor.over_time():
            random.shuffle(query_plans)

            for query_plan in query_plans:
                for i, trade_api_response in enumerate(TradeApiInterface.fetch_responses(query_plan=query_plan)):
                    self.metrics.results += len(trade_api_response.results)

                    valid_results = [result for result in trade_api_response.results if self._validator.is_valid(result)]
                    self.metrics.valid_results += len(valid_results)

                    yield valid_results

