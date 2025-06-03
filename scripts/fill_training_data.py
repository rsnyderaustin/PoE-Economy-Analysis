from data_handling import ListingBuilder
from file_management import Poe2DbModsManagerFile

print("Entered Python file for fill_training_data.py")

import logging

import psql
from operations_coordination.populate_training_data import TrainingDataPopulator

logging.basicConfig(level=logging.INFO)

print("Loading PSQL manager.")
psql_manager = psql.PostgreSqlManager(skip_sql=False)

listing_builder = ListingBuilder()

print("Loading TrainingDataPopulator class object.")
tdp = TrainingDataPopulator(listing_builder=listing_builder,
                            psql_manager=psql_manager)

print("Starting TrainingDataPopulator.fill_training_data function")
tdp.fill_training_data()
