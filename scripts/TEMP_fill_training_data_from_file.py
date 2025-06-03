from data_handling import ListingBuilder
from file_management import RawListingsFile
from operations_coordination.populate_training_data import TrainingDataPopulator
from psql import PostgreSqlManager

rlf = RawListingsFile()

listing_builder = ListingBuilder()
psql_manager = PostgreSqlManager()

populator = TrainingDataPopulator(
    listing_builder=listing_builder,
    psql_manager=psql_manager
)

populator.fill_training_data_from_listings_file(rlf)
