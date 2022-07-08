import os
import shutil
import time

from flask import Flask, request, jsonify, make_response, send_file, send_from_directory, g

from fate_arch.common import conf_utils
from fate_flow.utils.api_utils import federated_api
from fate_flow.extension.common import file_utils
from fate_flow.extension.utils import predict_file_utils
from fate_flow.extension.utils import deploy_utils
from fate_flow.utils.api_utils import get_json_result
from fate_flow.settings import FATE_FLOW_SERVICE_NAME, API_VERSION

ip = conf_utils.get_base_config(FATE_FLOW_SERVICE_NAME).get("host")
http_port = conf_utils.get_base_config(FATE_FLOW_SERVICE_NAME).get("http_port")

@manager.route('/test')
def test():
    response = {'test':'hello word'}
    return jsonify(response)


# @manager.route('/hello', methods=['post'])
# @login_required
# def hello():
#     return get_json_result(retcode=0, retmsg='success')

@manager.route('/find_status', methods=['post'])
def update_status():
    request_data = request.json
    service_id = request_data["service_id"]
    response = predict_file_utils.find_status(service_id)
    return jsonify(response)


@manager.route('/upload_file', methods=['post'])
def upload_file():
    data_file = request.files.get('file')
    request_data = request.form
    config_data = {'service_id': request_data.get("service_id"),
                   'context': request_data.get("context")}
    service_id = config_data["service_id"]
    context = config_data["context"]
    count = predict_file_utils.select_by_service_id_count(service_id)
    if count != 0:
        # predict_file = predict_file_utils.select_by_service(service_id)
        # status = predict_file["f_status"]
        # if status==1:
        str_time = str(int(time.time()))
        file_path, status = upload(data_file)
        if status == 0:
            msg = "成功上传"
            data = predict_file_utils.update_file(service_id, context, str_time, file_path, msg, status)
            grpc_status(service_id)
            return get_json_result(retcode=0, retmsg='success')
        else:
            # return get_json_result(retcode=50002, retmsg='已有service_id：' + service_id + ' 的上传记录')
            return get_json_result(retcode=50002, retmsg='上传失败')
    file_name, status = upload(data_file)
    if status == 0:
        msg = "成功上传"
    data_path = file_name
    context = config_data["context"]
    str_time = str(int(time.time()))
    data = predict_file_utils.insert_predict(service_id=service_id, status=status, msg=msg, str_time=str_time,
                                             data_path=data_path, context=context)
    grpc_status(service_id)
    return get_json_result(retcode=0, retmsg='success')


@manager.route('/update_file', methods=['post'])
def update_file():
    request_data = request.form
    config_data = {'service_id': request_data.get("service_id"),
                   'context': request_data.get("context")}
    # config_data = {'id': request_data.get("id"),
    #                'context': request_data.get("context")}
    file_path, status = upload(request.files.get('file'))
    service_id = config_data["service_id"]
    context = config_data["context"]
    str_time = str(int(time.time()))
    if status == 0:
        msg = "成功上传"
    data = predict_file_utils.update_file(service_id,context, str_time, file_path, msg, status)

    # data_info = predict_file_utils.select_by_id(service_id)
    # service_id = data_info["f_service_id"]
    response = deploy_utils.select_by_server_id(service_id)
    if response["retcode"] != 0:
        return jsonify(response)

    deploy_status = response["data"]["f_status"]
    if deploy_status == '1':
        return get_json_result(retcode=0, retmsg='success', data=data)

    grpc_status(service_id)
    return get_json_result(retcode=0, retmsg='success', data=data)


@manager.route('/predict/find_list', methods=['POST'])
def predict_find_list():
    request_data = request.json
    page = int(request_data.get('page', 1))
    page_length = int(request_data.get('page_length', 10))
    count = predict_file_utils.predict_file_count()
    data = predict_file_utils.select_by_list(page, page_length)
    return jsonify({
        'retcode': 0,
        'retmsg': 'success',
        'data': data,
        'page': page,
        'count': count,
        'page_length': page_length
    })


@manager.route('/predict/find_id', methods=['POST'])
def predict_find_id():
    request_data = request.json
    id = request_data["id"]
    data = predict_file_utils.select_by_id(id)
    file_name = data['f_data_path']
    # t = time.time()
    response = make_response(send_file(filename_or_fp=file_name, as_attachment=True))
    # response.headers["Content-Disposition"] = "attachment; filename={};".format(t)
    # return response
    return get_json_result(retcode=0, retmsg='success', data=data)


@manager.route('/predict/del', methods=['POST'])
def predict_del():
    request_data = request.json
    id = request_data["id"]
    data = predict_file_utils.select_by_id(id)
    filename = data["f_data_path"]
    if os.path.exists(filename):
        os.remove(filename)
    predict_file_utils.delete_predict(id)
    return get_json_result(retcode=0, retmsg='success')


def upload(data_file):
    dir_name = os.path.join(file_utils.get_project_base_directory(), 'data', 'upload')
    str_time = str(int(time.time()))
    file_path = file_utils.rename_file('upload_' + str_time, data_file.filename)
    file_name = os.path.join(dir_name, file_path)
    # print(file_name)
    os.makedirs(os.path.dirname(file_name), exist_ok=True)
    try:
        data_file.save(file_name)
    except Exception as e:
        shutil.rmtree(file_name)
        raise e
    status = 0
    return file_name, status


def grpc_status(service_id):
    response = deploy_utils.select_by_server_id(service_id)
    if response["retcode"] != 0:
        return response

    id = response["data"]["f_id"]
    config_data = {"service_id": service_id}
    info = deploy_utils.find_job_info(id)
    if info["retcode"] != 0:
        return jsonify(info)

    info = info["data"]
    job_id = info["job_id"]
    response_host = deploy_utils.grpc_deploy_command(job_id=job_id, method="POST", job_info=info,
                                                     json_body=config_data, endpoint='/predict_data/find_status')
    flag = True
    for r in response_host["host"]:
        if int(response_host["host"][r]["retcode"]) != 0 or int(response_host["host"][r]["status"]) != 0 :
            flag = False
            break
    if flag:
        if int(response_host["retcode"]) == 0:
            config_data = {"status": "1", "service_id": service_id}
            response = federated_api(job_id=job_id,
                                     method="POST",
                                     endpoint='/deploy/grpc/update_status',
                                     src_party_id=info["initiator"]["party_id"],
                                     dest_party_id=info["role"]["guest"][0],
                                     src_role=info["initiator"]["role"],
                                     json_body=config_data,
                                     federated_mode="MULTIPLE")

@manager.route('/predict/condition_list', methods=['POST'])
def query_predict_file():
    predicts, page, page_length, count = predict_file_utils.query_predict(**request.json)
    if not predicts:
        return get_json_result(retcode=0, retmsg='no predict_file could be found', data=[])
    return jsonify({
        'retcode': 0,
        'retmsg': 'success',
        'data': [predict.to_json() for predict in predicts],
        'page': page,
        'count': count,
        'page_length': page_length
    })