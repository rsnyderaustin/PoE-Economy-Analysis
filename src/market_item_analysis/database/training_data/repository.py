from datetime import datetime, timezone, timedelta

from sqlalchemy import select, Select, insert

from src.market_item_analysis.core.enums.trade import ListedSince
from src.market_item_analysis.database.training_data.model import TrainingDataModel
from src.market_item_analysis.trade_api.raw_result import TradeApiResult


class TrainingDataRepository:

    def __init__(self, session):
        self.session = session

    def insert_results(self, results: list[TradeApiResult]):
        """
        Performs a bulk insert of TradeApiResult objects into the database.
        """
        if not results:
            return

        # Prepare the list of dictionaries for bulk insert
        # We assume TradeApiResult has an as_dict() method or accessible attributes
        data_to_insert = [result.to_training_results_model() for result in results]

        # Execute the bulk insert
        self.session.execute(
            insert(TrainingDataModel),
            data_to_insert
        )

    def _stmt_to_results(self, stmt: Select) -> list[TradeApiResult]:
        models = self.session.execute(stmt).scalars().all()

        results = [TradeApiResult(m.listing_object) for m in models]

        return results

    def fetch_all_results(self) -> list[TradeApiResult]:
        stmt = select(TrainingDataModel.result_object)

        return self._stmt_to_results(stmt=stmt)

    def fetch_recent_results(self, listed_since: ListedSince) -> list[TradeApiResult]:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=listed_since.minutes_equivalent)
        stmt = select(TrainingDataModel.result_object).where(
            TrainingDataModel.indexed_datetime_utc >= cutoff
        )

        return self._stmt_to_results(stmt=stmt)
