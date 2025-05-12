from file_management import FileKey, FilesManager
from operations_coordination.operations_coordinator import OperationsCoordinator

listings = FilesManager().file_data[FileKey.CRITICAL_PRICE_PREDICT_TRAINING]
ops_coord = OperationsCoordinator()
ops_coord.fill_training_data()
# ops_coord.build_price_predict_model()
# ops_coord.find_underpriced_items()
