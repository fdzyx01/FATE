import json
import os
import shutil
import time

import requests
from flask import Flask, request, jsonify, make_response, send_file, send_from_directory, g

from fate_arch.common import conf_utils
from fate_flow.extension.common import file_utils
from fate_flow.extension.utils import predict_utils, deploy_utils
from fate_flow.utils.api_utils import get_json_result
from fate_flow.settings import FATE_FLOW_SERVICE_NAME, API_VERSION

ip = conf_utils.get_base_config(FATE_FLOW_SERVICE_NAME).get("host")
http_port = conf_utils.get_base_config(FATE_FLOW_SERVICE_NAME).get("http_port")
serving_ip = conf_utils.get_base_config("servings", {}).get("hosts")[0][:-5]
server_url = "http://" + serving_ip + ":8350/api"


# @manager.route('/download', methods=['get'])
# def download():
#     file_id = request.args.get("id")
#     file_path = os.path.join(file_utils.get_project_base_directory(), 'batch')
#     print(os.path.join(file_path, 'batch_' + file_id + '.csv'))
#     response = make_response(send_from_directory(file_path, 'batch_' + file_id + '.csv', as_attachment=True))
#     return response


@manager.route('/hello', methods=['post'])
def hello():
    return get_json_result(retcode=0, retmsg='success')


@manager.route('/download', methods=['get'])
def download():
    file_id = request.args.get("id")
    file_path = os.path.join(file_utils.get_project_base_directory(), 'batch_score')
    response = make_response(send_from_directory(file_path, 'score_' + file_id + '.csv', as_attachment=True))
    return response


@manager.route('/single', methods=['post'])
def single():
    request_data = request.json
    feature_id = request_data.get("feature_id")
    feature_id["service_id"] = request_data.get("service_id")
    sendToRemoteFeatureData = feature_id
    config_data = {"serviceId": request_data.get("service_id"), "sendToRemoteFeatureData": sendToRemoteFeatureData,
                   "featureData": request_data.get("feature_data"), "model_version": "123"}
    session_token = get_session()
    headers = {"sessionToken": session_token}
    url = server_url + "/validate/inference"
    response = requests.post(url, json=config_data, headers=headers)
    response_json = json.loads(response.text)
    if response_json["data"]["retcode"] !=0:
        if response_json["data"]["retcode"] == 2113:
            info = {"retcode": 401, "retmsg": "id no exist", "data": {}}
        else:
            info = {"retcode": 401, "retmsg": response_json["data"]["retmsg"], "data": {}}
    else:
        info = {"retcode": 0, "retmsg": "", "data":{"score": response_json["data"]["data"]["score"]}}
    return jsonify(info)


@manager.route('/batch', methods=['post'])
def batch():
    request_data = request.form
    config_data = {"serviceId": request_data.get("service_id"), "batchDataList": []}
    service_id = request_data.get("service_id")
    data_file = request.files.get('file')
    birth_data = predict_utils.birth_data(data_file)
    config_data["batchDataList"] = predict_utils.birth_json_data(birth_data, service_id)

    str_time = str(int(time.time()))
    new_file_data = predict_utils.save_data("batch_data", "data_", str_time, data_file)
    try:
        data_file.seek(0)
        data_file.save(new_file_data)
    except Exception as e:
        shutil.rmtree(new_file_data)
        raise e

    session_token = get_session()
    headers = {"sessionToken": session_token}
    response = requests.post(server_url + "/validate/batchInference", json=config_data, headers=headers)
    response_data = json.loads(response.text)["data"]
    if response_data["retcode"] == 0:
        batchDataList = response_data["batchDataList"]
        new_file = predict_utils.save_data("batch_score", "score_", str_time, data_file)
        predict_utils.save_score_data(birth_data, batchDataList, new_file)
        name = request_data["name"]
        service_id = int(request_data["service_id"])
        context = request_data["context"]
        predict_utils.add_predict_batch(name=name, service_id=service_id, context=context, status=response_data["retcode"], msg=response_data["retmsg"], old_path=new_file_data,  new_path=new_file, str_time=str_time)
        # response = {"retcode": 0, "retmsg": "success",
        #             "data": {"file_path": "/{}".format(API_VERSION) + "/predict/download?id=" + str_time + str_time}}

        url = "http://{}:{}/{}".format(ip, http_port, API_VERSION)
        config_data = {"status": "3", "service_id": service_id}
        response = requests.post("/".join([url, "deploy", "grpc/update_status"]), json=config_data).json()
        if response["retcode"] != 0:
            return jsonify(response)

        response = {"retcode": 0, "retmsg": "success"}
        return jsonify(response)
    else:
        response = {"retcode": response_data["retcode"], "retmsg": response_data["retmsg"]}
        return jsonify(response)


@manager.route('/delete', methods=['post'])
def delete():
    id = int(request.json.get("id"))
    response = predict_utils.del_predict_batch(id)
    if response["row"] != 0:
        try:
            os.remove(response["data_path"])
            os.remove(response["score_path"])
        except:
            raise Exception('remove job file failed')
    return get_json_result(retcode=0, retmsg='success')


@manager.route('/searchone', methods=['post'])
def searchone():
    data_id = request.json.get("id")
    find = predict_utils.select_one(data_id)
    return jsonify(find)


@manager.route('/list', methods=['post'])
def select_list():
    page = int(request.json.get('page', 1))
    length = int(request.json.get('page_length'))
    count = predict_utils.select_count()
    if count == 0:
        return jsonify({
            'retcode': 100,
            'retmsg': 'list is empty',
            'data': {}
        })
    page_len = count // length
    mod = count % length
    if mod != 0: page_len = page_len + 1
    if page > page_len: page = page_len
    find = predict_utils.select_page_length(page, length)
    index = 0
    lists = []
    while index < len(find):
        lists.append({
            'f_id': find[index].f_id,
            'f_name': find[index].f_name,
            'f_service_id': find[index].f_service_id,
            'f_context': find[index].f_context,
            'f_status': find[index].f_status,
            'f_msg': find[index].f_msg,
            'f_update_time': find[index].f_update_time,
            'f_data_path': find[index].f_data_path,
            'f_score_path': find[index].f_score_path
        })
        index += 1
    return jsonify({
        'retcode': 0,
        'retmsg': 'success',
        'data': lists,
        'page': page,
        'count': count,
        'page_length': length
    })


def get_session():
    user_info = {"password": "admin", "username": "admin"}
    url = server_url + "/admin/login"
    response = requests.post(url, json=user_info)
    response_json = json.loads(response.text)
    session_token = response_json["data"]["sessionToken"]
    return session_token
