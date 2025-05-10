import file_management


def _determine_dict_length(data: dict):
    return max([len(v) for v in data.values()])


class PricePredictDataManager:

    def __init__(self):
        files_manager = file_management.FilesManager

        self.training_data = files_manager.file_data[FileKey.CRITICAL_PRICE_PREDICT_TRAINING]
        self.training_data_length = _determine_dict_length(self.training_data)

        self.search_data = {col: [] for col in self.training_data.keys()}

        self.search_data_length = 0

    def add_training_data(self, new_data: dict):
        for col, value in new_data.items():
            if col not in self.training_data:
                self.training_data[col_name] = [None for _ in list(range(self.training_data_length))]
            self.training_data[col].append(val)

        leftover_cols = [col for col in self.training_data.keys() if col not in new_data.keys()]
        
        for col in leftover_cols:
            self.training_data[col].append(None)

    def add_search_data(self, search_data: dict):
        if not self.search_data:
            # If there is currently no search data then our only hope is filling column structure from training data
            if self.training_data:
                self.search_data = {col: [] for col in self.training_data.keys()}
            else:
                raise ValueError(f"Cannot add PricePredict search data. No training data to determine column structure.")

        for col, value in search_data.items():
            if col not in self.search_data:
                raise KeyError(f"Column {col} not in PricePredict search data. All columns from training data must be "
                               f"present when adding data.")
            self.search_data[col].append(value)

