
from operations_coordination.operations_coordinator import OperationsCoordinator


ops_coord = OperationsCoordinator(refresh_poecd_source=False)
# ops_coord.fill_training_data()
ops_coord.build_price_predict_model()
# ops_coord.find_underpriced_items()