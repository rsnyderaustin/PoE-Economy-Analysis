
import json
import os


class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return super().default(obj)


def write_to_file(file_path, data, disable_temp: bool = False):
    disable_temp = True # This is literally just for work

    if file_path.suffix == '.json':
        if disable_temp:
            with open(file_path, 'w') as training_data_json_path:
                json.dump(data, training_data_json_path, indent=4, cls=SetEncoder)
                training_data_json_path.flush()
                os.fsync(training_data_json_path.fileno())

        else:
            tmp_path = file_path + ".tmp"
            with open(tmp_path, 'w') as training_data_json_path:
                json.dump(data, training_data_json_path, indent=4, cls=SetEncoder)
                training_data_json_path.flush()
                os.fsync(training_data_json_path.fileno())

            os.replace(tmp_path, file_path)
    elif file_path.suffix == '.csv':
        data.to_csv(file_path)


