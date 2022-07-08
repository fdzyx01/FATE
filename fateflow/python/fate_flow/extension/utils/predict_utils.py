import os
import csv

from fate_arch.common import file_utils, conf_utils
from fate_flow.extension.model.db_models import DB, Predict


@DB.connection_context()
def add_predict_batch(name,service_id, old_path, context, status, msg, new_path, str_time):
    data = Predict.create(f_name=name, f_service_id=service_id, f_context=context,
                          f_status=status, f_data_path=old_path, f_msg=msg, f_score_path=new_path, f_create_time=str_time)


@DB.connection_context()
def select_count():
    count = Predict.select().count()
    return count


@DB.connection_context()
def del_predict_batch(id):
    file = Predict.select().where(Predict.f_id == id).get()
    response = {"data_path": file.f_data_path, "score_path": file.f_score_path}
    row = file.delete_instance()
    response["row"] = row
    return response


@DB.connection_context()
def select_one(data_id):
    try:
        find = Predict.select().where(Predict.f_id == data_id).get()
        return {
            'f_id': find.f_id,
            'f_name': find.f_name,
            'f_service_id': find.f_service_id,
            'f_context': find.f_context,
            'f_status': find.f_status,
            'f_msg': find.f_msg,
            'f_update_time': find.f_update_time,
            'f_data_path': find.f_data_path,
            'f_score_path': find.f_score_path
        }
    except:
        return {
            'retcode': 401,
            'retmsg': 'Query failed '
        }


@DB.connection_context()
def select_page_length(page, length):
    list = Predict.select().order_by(Predict.f_create_time.desc()).paginate(page, length)
    return list


def birth_data(data_file):
    config_data = data_file.read().decode('utf-8').split("\r\n")
    data_y = len(config_data)
    for i in range(data_y):
        config_data[i] = config_data[i].split(",")
    return config_data


def birth_json_data(birth_data, service_id):
    data_y = len(birth_data)
    data_x = len(birth_data[0])
    data_json = []
    for i in range(1, data_y - 1):
        send_data = {"id": int(birth_data[i][0]), "service_id": service_id}
        feature_data = {}
        for j in range(1, data_x):
            feature_data[birth_data[0][j]] = float(birth_data[i][j])
        data_json.append({"sendToRemoteFeatureData": send_data, "featureData": feature_data})
    return data_json


def save_data(file_name, prefix, str_time_data, data_file):
    dir_name_data = os.path.join(file_utils.get_project_base_directory(), file_name)
    file_path_data = file_utils.rename_file(prefix + str_time_data, data_file.filename)
    new_file_data = os.path.join(dir_name_data, file_path_data)
    os.makedirs(os.path.dirname(new_file_data), exist_ok=True)
    return new_file_data


def save_score_data(birth_data, batchDataList, new_file):
    if not os.path.exists(new_file):
        with open(new_file, "w", newline='') as f:
            writer = csv.writer(f)
            birth_data[0].append("score")
            writer.writerow(birth_data[0])
            for i in range(len(batchDataList)):
                if batchDataList[i]["retcode"] == 0:
                    if "score" in batchDataList[i]["data"].keys():
                        birth_data[i + 1].append(batchDataList[i]["data"]["score"])
                    else:
                        birth_data[i + 1].append("none")
                    writer.writerow(birth_data[i + 1])
                else:
                    birth_data[i + 1].append("id does not exist")
                    writer.writerow(birth_data[i + 1])
            f.close()
