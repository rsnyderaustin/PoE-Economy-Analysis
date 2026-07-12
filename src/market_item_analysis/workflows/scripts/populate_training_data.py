from src.market_item_analysis.core.enums.trade import ListedSince
from src.market_item_analysis.core.input_output_service import InputOutputService
from src.market_item_analysis.database.postgres_manager import PostgresManager, PostgresDatabaseUrl
from src.market_item_analysis.database.training_data.repository import TrainingDataRepository
from src.market_item_analysis.listing.objects import Listing
from src.market_item_analysis.workflows.query_plan_presets import QueryPlanPresets
from src.market_item_analysis.workflows.trade_api_results_ingestor import TradeApiResultsIngestor, \
    TradeApiResultValidator


def fetch_training_results_to_db():
    postgres_manager = PostgresManager(db_url=PostgresDatabaseUrl())

    with postgres_manager.get_session() as session:

        training_data_repo = TrainingDataRepository(session=session)

        recent_results = training_data_repo.fetch_recent_results(
            listed_since=ListedSince.UP_TO_1_HOUR
        )

        listings_validator = TradeApiResultValidator(existing_results=recent_results)
        ingestor = TradeApiResultsIngestor(validator=listings_validator)
        training_query_plans = QueryPlanPresets.standard_training(listed_since=ListedSince.UP_TO_1_HOUR)

        results_cache = []
        for trade_api_results in ingestor.ingest(query_plans=training_query_plans, pull_minutes_limit=5):
            results_cache.extend(trade_api_results)

            if len(results_cache) > 100:
                training_data_repo.insert_results(results=results_cache)
                results_cache = []

        if results_cache:
            training_data_repo.insert_results(results=results_cache)
