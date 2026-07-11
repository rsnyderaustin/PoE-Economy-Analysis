from src.market_item_analysis.core.input_output_service import InputOutputService
from src.market_item_analysis.listing.objects import EquipmentListing
from src.market_item_analysis.workflows.query_plan_presets import QueryPlanPresets
from src.market_item_analysis.workflows.trade_api_results_ingestor import TradeApiResultsIngestor


def populate_training_data():
    ingestor = TradeApiResultsIngestor()

    training_query_plans = QueryPlanPresets.standard_training()

    for trade_api_results in ingestor.ingest(query_plans=training_query_plans,
                                             pull_minutes_limit=5):
        listings = [EquipmentListing.from_api_response(r=r) for r in trade_api_results]
        listing_dicts = [listing.to_dict() for listing in listings]
        InputOutputService.to_jsonl(records=listing_dicts, path=)
