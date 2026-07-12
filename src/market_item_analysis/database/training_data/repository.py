from datetime import datetime, timezone, timedelta

from sqlalchemy import select, Select

from src.market_item_analysis.core.enums.trade import ListedSince
from src.market_item_analysis.database.training_data.model import TrainingDataModel
from src.market_item_analysis.trade_api.trade_result import TradeApiResult


class TrainingDataRepository:

    def __init__(self, session):
        self.session = session

    def _stmt_to_results(self, stmt: Select) -> list[TradeApiResult]:
        models = self.session.execute(stmt).scalars().all()

        results = [TradeApiResult(m.listing_object) for m in models]

        return results

    def fetch_all_results(self):
        stmt = select(TrainingDataModel.result_object)

        return self._stmt_to_results(stmt)

    def fetch_recent_results(self, listed_since: ListedSince) -> list[TradeApiResult]:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=listed_since.minutes_equivalent)
        stmt = select(TrainingDataModel.result_object).where(
            TrainingDataModel.indexed_datetime_utc >= cutoff
        )

        return self._stmt_to_results(stmt)
