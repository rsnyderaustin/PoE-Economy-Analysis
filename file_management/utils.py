
import json
import os


def write_to_file(file_path, data, disable_temp: bool = False):
    disable_temp = True # This is literally just for work
    if disable_temp:
        with open(file_path, 'w') as training_data_json_path:
            json.dump(data, training_data_json_path, indent=4)
            training_data_json_path.flush()
            os.fsync(training_data_json_path.fileno())

    else:
        tmp_path = file_path + ".tmp"
        with open(tmp_path, 'w') as training_data_json_path:
            json.dump(data, training_data_json_path, indent=4)
            training_data_json_path.flush()
            os.fsync(training_data_json_path.fileno())

        os.replace(tmp_path, file_path)


