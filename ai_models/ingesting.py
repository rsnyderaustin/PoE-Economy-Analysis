
import logging

from file_management import FilesManager, FileKey
from instances_and_definitions import ModifiableListing
from . import data_prep


class DataIngester:

    def __init__(self):
        self.files_manager = FilesManager()
        self.data_prep = data_prep.DataPrep()
        self.training_data = self.files_manager.file_data[FileKey.TRAINING_DATA]

    @property
    def num_rows(self):
        first_list = next(iter(self.training_data.values()))
        return len(first_list)

    def save_training_data(self, listings: list[ModifiableListing]):
        for listing in listings:
            flattened_listing = self.data_prep.format_listing_for_price_prediction(listing)
            for col_name, value in flattened_listing.items():
                if col_name not in self.training_data:
                    # We have to insert a value for each row since this column has been added
                    self.training_data[col_name] = [None for _ in list(range(self.num_rows))]
                self.training_data[col_name].append(value)

            # Append a new value for each column that wasn't a part of this listing data
            non_included_data_cols = [col for col in set(self.training_data.keys()) if col not in set(flattened_listing.keys())]
            for col_name in non_included_data_cols:
                self.training_data[col_name].append(None)

        logging.info(f"Writing {len(listings)} listings to training data.")

        self.files_manager.cache_training_data(self.training_data)



