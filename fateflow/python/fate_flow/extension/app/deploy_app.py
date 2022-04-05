import json
import time


import requests
from flask import Flask, request, jsonify, make_response, send_file, send_from_directory, g

from fate_arch.common import conf_utils
from fate_flow.extension.utils import predict_utils, deploy_utils, predict_file_utils
from fate_flow.utils.api_utils import get_json_result
from fate_flow.settings import FATE_FLOW_SERVICE_NAME, API_VERSION


ip = conf_utils.get_base_config(FATE_FLOW_SERVICE_NAME).get("host")
http_port = conf_utils.get_base_config(FATE_FLOW_SERVICE_NAME).get("http_port")


@manager.route('/create', methods=['POST'])
def insert_deploy():
    request_data = request.json
    service_id = request_data["service_id"]
    status = request_data["status"]
    location = request_data["location"]
    msg = request_data["msg"]
    model_id = request_data["model_id"]
    context = request_data["context"]
    str_time = str(int(time.time()))
    data = deploy_utils.insert_deploy(service_id=service_id, status=status, msg=msg, str_time=str_time, model_id= model_id, context=context, location=location)
    return get_json_result(retcode=0, retmsg='success', data=data)

@manager.route('/grpc/create', methods=['post'])
def load():
    request_data = request.json
    config_data = {'job_id': request_data.get("job_id"), 'service_id': str(int(time.time()))}
    # json.loads(json.dumps(str(int(time.time())).encode()))
    # print(str(int(time.time())).encode())
    print(json.loads(str(int(time.time())).encode()))
    url = "http://{}:{}/{}".format(ip, http_port, API_VERSION)
    response = requests.post("/".join([url, "job", "query"]), json=config_data)
    job_info = response.json()
    if len(job_info["data"]) == 0:
        return get_json_result(retcode=1, retmsg='no job could be found')
    de = {}
    de["model_id"] = job_info["data"][0]["f_runtime_conf_on_party"]["job_parameters"]["model_id"]
    de["model_version"] = job_info["data"][0]["f_runtime_conf_on_party"]["job_parameters"]["model_version"]
    rs = requests.post("/".join([url, "model", "deploy"]), json=de)
    deploy_info = rs.json()
    deploy_info["location"] = 1
    if deploy_info["retcode"] != 0:
        return jsonify(deploy_info)

    info = {
        "initiator": {},
        "role": {},
        "job_parameters": {}
    }
    info["initiator"]["party_id"] = job_info["data"][0]["f_initiator_party_id"]
    info["initiator"]["role"] = job_info["data"][0]["f_initiator_role"]
    info["role"]["guest"] = [str(i) for i in job_info["data"][0]["f_roles"]["guest"]]
    info["role"]["host"] = [str(i) for i in job_info["data"][0]["f_roles"]["host"]]
    info["role"]["arbiter"] = [str(i) for i in job_info["data"][0]["f_roles"]["arbiter"]]
    # info["job_parameters"]["work_mode"] = job_info["data"][0]["f_runtime_conf_on_party"]["job_parameters"]["work_mode"]
    info["job_parameters"]["work_mode"] = 1
    info["job_parameters"]["model_id"] = deploy_info["data"]["model_id"]
    info["job_parameters"]["model_version"] = deploy_info["data"]["model_version"]
    info["job_parameters"]["file_path"] = ""

    r = requests.post("/".join([url, "model", "load"]), json=info)
    load_info = r.json()
    load_info["location"] = 2
    if load_info["retcode"] != 0:
        return jsonify(load_info)

    info_b = {
        "service_id": "",
        "initiator": {},
        "role": {},
        "job_parameters": {},
        "servings": []
    }
    info_b["service_id"] = config_data["service_id"]
    info_b["initiator"]["party_id"] = job_info["data"][0]["f_initiator_party_id"]
    info_b["initiator"]["role"] = job_info["data"][0]["f_initiator_role"]
    info_b["role"]["guest"] = [str(i) for i in job_info["data"][0]["f_roles"]["guest"]]
    info_b["role"]["host"] = [str(i) for i in job_info["data"][0]["f_roles"]["host"]]
    info_b["role"]["arbiter"] = [str(i) for i in job_info["data"][0]["f_roles"]["arbiter"]]
    # info_b["job_parameters"]["work_mode"] = job_info["data"][0]["f_runtime_conf_on_party"]["job_parameters"]["work_mode"]
    info_b["job_parameters"]["work_mode"] = 1
    info_b["job_parameters"]["model_id"] = job_info["data"][0]["f_runtime_conf_on_party"]["job_parameters"]["model_id"]
    info_b["job_parameters"]["model_version"] = deploy_info["data"]["model_version"]
    rs = requests.post("/".join([url, "model", "bind"]), json=info_b)
    bind_info = rs.json()
    bind_info["location"] = 3

    service_id = int(config_data["service_id"])
    status = bind_info["retcode"]
    model_id = request_data["job_id"]
    location = bind_info["location"]
    context = request_data["context"]
    msg = bind_info["retmsg"]
    str_time = str(int(time.time()))
    data = deploy_utils.insert_deploy(service_id=service_id, status=status, location=location, msg=msg, str_time=str_time,
                                      model_id=model_id, context=context)
    command_body = {
        'service_id': config_data["service_id"],
        'status': bind_info["retcode"],
        'model_id': request_data["job_id"],
        'location': bind_info["location"],
        'context': request_data["context"],
        'msg': bind_info["retmsg"],
        'str_time': str(int(time.time()))
    }
    response = deploy_utils.grpc_deploy_command(job_id=request_data.get("job_id"), method="POST", job_info=info,
                                                json_body=command_body, endpoint='/deploy/create')
    if response["retcode"] != 0:
        response["location"] = 3
        return jsonify(response)

    response_info = {}
    response_info["retcode"] = 0
    response_info["retmsg"] = "success"
    response_info["location"] = 3
    return jsonify(response_info)

@manager.route('/find_id', methods=['POST'])
def deploy_find_id():
    request_data = request.json
    id = request_data["id"]
    data = deploy_utils.select_by_id(id)
    return jsonify(data)


@manager.route('/find_list', methods=['POST'])
def deploy_find_list():
    request_data = request.json
    page = int(request_data.get('page', 1))
    page_length = int(request_data.get('page_length', 10))
    count = deploy_utils.select_count()
    data = deploy_utils.select_by_list(page, page_length)
    return jsonify({
        'retcode': 0,
        'retmsg': 'success',
        'data': data,
        'page': page,
        'count': count,
        'page_length': page_length
    })
@manager.route('/find_deploy_list', methods=['get'])
def deployed_list():
    status = int(request.args.get("status"))
    data = deploy_utils.select_deploy_list(status)
    return jsonify({
        'retcode': 0,
        'retmsg': 'success',
        'data': data
    })
@manager.route('/deploy/condition_list', methods=['POST'])
def query_deploy():
    deploys, page, page_length, count = deploy_utils.query_deploy(**request.json)
    if not deploys:
        return get_json_result(retcode=0, retmsg='no deploy could be found', data=[])
    return jsonify({
        'retcode': 0,
        'retmsg': 'success',
        'data': [deploys.to_json() for deploys in deploys],
        'page': page,
        'count': count,
        'page_length': page_length
    })
@manager.route('/del', methods=['POST'])
def deploy_del():
    request_data = request.json
    id = request_data["id"]
    deploy_utils.delete_deploy(id)
    return get_json_result(retcode=0, retmsg='success')

@manager.route('/http/del', methods=['POST'])
def del_service_id():
    request_data = request.json
    service_id = request_data["service_id"]
    deploy_utils.del_by_service_id(service_id)
    return get_json_result(retcode=0, retmsg='success')

@manager.route('/grpc/del', methods=['post'])
def grpc_delete():
    request_data = request.json
    id = request_data["id"]
    info = deploy_utils.find_job_info(id)
    if info["retcode"] != 0:
        return jsonify(info)

    job_id = info["data"]["job_id"]
    config_data = {"service_id": info["data"]["service_id"]}
    print(config_data)
    response = deploy_utils.grpc_deploy_command(job_id=job_id, method="POST", job_info=info["data"],
                                                json_body=config_data, endpoint='/deploy/http/del')
    deploy_utils.delete_deploy(id)
    response["guest"] = {
        'retcode': 0,
        'retmsg': 'success'
    }
    return jsonify(response)

@manager.route('/update_status', methods=['post'])
def update_status():
    request_data = request.json
    status = request_data["status"]
    service_id = request_data["service_id"]
    deploy_utils.update_status(service_id, status)
    if status == 0:
        predict_file_utils.update_status(service_id, 1)
    return get_json_result(retcode=0, retmsg='success')

@manager.route('/grpc/update_status', methods=['post'])
def grpc_update_status():
    request_data = request.json
    status = request_data["status"]
    service_id = request_data["service_id"]

    response = deploy_utils.select_by_server_id(service_id)
    if response["retcode"] != 0:
        return response

    id = response["data"]["f_id"]
    config_data = {"service_id": service_id, "status": status}
    info = deploy_utils.find_job_info(id)
    if info["retcode"] != 0:
        return jsonify(info)

    job_id = info["data"]["job_id"]
    response = deploy_utils.grpc_deploy_command(job_id=job_id, method="POST", job_info=info["data"],
                                                json_body=config_data, endpoint='/deploy/update_status')
    deploy_utils.update_status(service_id, status)
    response["guest"] = {
        'retcode': 0,
        'retmsg': 'success'
    }
    return jsonify(response)


