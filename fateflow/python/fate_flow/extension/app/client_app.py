import json
import os
import shutil
import subprocess
import sys
import time

import requests
from flask import Flask, request, jsonify, make_response, send_file, send_from_directory, g
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor

from fate_arch.common import conf_utils
from fate_flow.extension.common import file_utils
from fate_flow.settings import stat_logger
from fate_flow.extension.utils import job_utils
from fate_flow.utils.api_utils import get_json_result
from fate_flow.settings import FATE_FLOW_SERVICE_NAME, API_VERSION

ip = conf_utils.get_base_config(FATE_FLOW_SERVICE_NAME).get("host")
http_port = conf_utils.get_base_config(FATE_FLOW_SERVICE_NAME).get("http_port")
server_url = "http://{}:{}/{}".format(ip, http_port, API_VERSION)
fate_flow_path = os.path.join(file_utils.get_project_base_directory(),"fate_flow", "fate_flow_client.py")


@manager.errorhandler(500)
def internal_server_error(e):
    stat_logger.exception(e)
    return get_json_result(retcode=100, retmsg=str(e))

@manager.route('/upload', methods=['post'])
def upload_conf_file():
    request_data = request.form
    # config_data = {'table_name': request_data.get("table_name"), 'namespace': request_data.get("namespace"), 'head': 1,
    #                'partition': 16, 'work_mode': 0}
    config_data = {'table_name': request_data.get("table_name"), 'data_type': request_data.get("data_type"),
                   'description': request_data.get("description"),'work_mode': request_data.get("work_mode"),
                   'namespace':"experiment",'head': 1, 'partition': 16}
    data_file = request.files.get('file')
    dir_name = os.path.join(file_utils.get_project_base_directory(), 'data', 'upload')
    str_time = str(int(time.time()))
    file_path = file_utils.rename_file('config_' + str_time, data_file.filename)
    file_name = os.path.join(dir_name, file_path)
    os.makedirs(os.path.dirname(file_name), exist_ok=True)
    config_data['file'] = file_name
    try:
        data_file.save(file_name)
    except Exception as e:
        shutil.rmtree(file_name)
        raise e
    if os.path.exists(file_name):
        with open(file_name, 'rb') as fp:
            # octet-stream表明他就是一个字节流
            data = MultipartEncoder(
                fields={'file': (os.path.basename(file_name), fp, 'application/octet-stream')}
            )
            tag = [0]

            def read_callback(monitor):
                if config_data.get('verbose') == 1:
                    sys.stdout.write("\r UPLOADING:{0}{1}".format("|" * (monitor.bytes_read * 100 // monitor.len),
                                                                  '%.2f%%' % (monitor.bytes_read * 100 // monitor.len)))
                    sys.stdout.flush()
                    if monitor.bytes_read / monitor.len == 1:
                        tag[0] += 1
                        if tag[0] == 2:
                            sys.stdout.write('\n')

            data = MultipartEncoderMonitor(data, read_callback)
            response = requests.post("/".join([server_url, "data", "upload"]), data=data,
                                     params=config_data,
                                     headers={'Content-Type': data.content_type})
    else:
        raise Exception('The file is obtained from the fate flow client machine, but it does not exist, '
                        'please check the path: {}'.format(file_name))
    response = json.loads(response.text)
    return jsonify(response)

@manager.route('/submit/job/general', methods=['post'])
def submit_job_general():
    request_data = request.json
    runtime_config, dsl_path = create_new_runtime_config(request_data)
    job_id = exec_task(runtime_config, dsl_path)
    data = {"job_id": job_id}
    job_name = request_data["job_name"]
    job_description = request_data["job_description"]
    date = job_utils.insert_job(job_description=job_description, job_name=job_name, job_id=job_id)
    return get_json_result(retcode=0, retmsg='success', data=data)

# @manager.route('/submit/job/intersection', methods=['post'])
# def submit_job_general_intersection():
#     request_data = request.json
#     conf_path, dsl_path = create_new_runtime_config_intersection(request_data)
#     job_id = exec_task(conf_path, dsl_path)
#     data = {"job_id": job_id}
#     job_name = request_data["job_name"]
#     job_description = request_data["job_description"]
#     date = job_utils.insert_job(job_description=job_description, job_name=job_name, job_id=job_id)
#     return get_json_result(retcode=0, retmsg='success', data=data)

@manager.route('/submit/job/high', methods=['post'])
def submit_job_high():
    config_file = request.files.get('config_file')
    str_time = str(int(time.time()))
    config_file_name = file_utils.rename_file('config_' + str_time, config_file.filename)
    dsl_file = request.files.get('dsl_file')
    dsl_file_name = file_utils.rename_file('dsl_' + str_time, dsl_file.filename)
    request_data = request.form
    filename = os.path.join(file_utils.get_project_base_directory(), 'data', 'upload',
                            request_data['train_algorithm_name'])
    config_file_path = os.path.join(filename, config_file_name)
    os.makedirs(os.path.dirname(config_file_path), exist_ok=True)
    dsl_file_path = os.path.join(filename, dsl_file_name)
    os.makedirs(os.path.dirname(dsl_file_path), exist_ok=True)
    try:
        config_file.save(config_file_path)
    except Exception as e:
        shutil.rmtree(config_file_path)
        raise e
    try:
        dsl_file.save(dsl_file_path)
    except Exception as e:
        shutil.rmtree(dsl_file_path)
        raise e
    config_data = {}
    with open(config_file_path, 'r') as f:
        config_data = json.load(f)
    config_data['dsl'] = dsl_file_path
    config_data['config'] = config_file_path

    dsl_data = {}
    if dsl_file_path or config_data.get('job_parameters', {}).get('job_type', '') == 'predict':
        if dsl_file_path:
            dsl_path = os.path.abspath(dsl_file_path)
            with open(dsl_path, 'r') as f:
                dsl_data = json.load(f)
    else:
        raise Exception('the following arguments are required: {}'.format('dsl path'))
    post_data = {'job_dsl': dsl_data,
                 'job_runtime_conf': config_data}
    response = requests.post("/".join([server_url, "job", "submit"]), json=post_data)
    response = json.loads(response.text)
    data = {"job_id": response["jobId"]}
    return get_json_result(retcode=0, retmsg='success', data=data)


@manager.route('/download/template', methods=['post'])
def download_template():
    config_data = request.json
    file_name = config_data['file_name']
    t = time.time()
    response = make_response(send_file(filename_or_fp=file_name, as_attachment=True))
    response.headers["Content-Disposition"] = "attachment; filename={};".format(t)
    return response

@manager.route('/download/conf_params', methods=['get'])
def download_params():
    # config_data = request.json
    params_name = request.args.get("params_name")
    # params_name = config_data['params_name']
    params_dir = os.path.abspath(os.path.join(file_utils.get_project_base_directory()))
    params_dir = os.path.join(params_dir, "fate_flow/extension/conf/params_conf/conf_params_path.json")
    with open(params_dir, "r") as fin:
        params_dir_dict = json.loads(fin.read())
    if not params_dir_dict:
        if not os.path.isfile(params_dir_dict):
            raise ValueError("config file {} dose not exist, please check!".format(params_dir))
        raise ValueError("{} ")
    # params_name = config_data['params_name']
    if params_name in params_dir_dict:
        params_path = params_dir_dict[params_name]["conf_params"]
    else:
        raise ValueError("algorithm {} dose not exist, please check!".format(params_name))
    params_path = os.path.abspath(os.path.join(file_utils.get_project_base_directory(), params_path))
    # return get_json_result(retcode=0, retmsg='success', data=params_path)
    # t = time.time()
    response = make_response(send_file(filename_or_fp=params_path, as_attachment=True))
    response.headers["Content-Type"] = "application/octet-stream; filename="+params_name+".docx"
    return response


@manager.route('/login', methods=['post'])
def login():
    login_info = request.json
    party_username = conf_utils.get_base_config("role_info").get("username")
    party_password = conf_utils.get_base_config("role_info").get("password")
    if party_username != login_info["username"]:
        return get_json_result(retcode=101, retmsg="用户不存在")
    if party_password != login_info["password"]:
        return get_json_result(retcode=102, retmsg="密码错误")
    party_name = conf_utils.get_base_config("role_info").get("party_name")
    party_id = conf_utils.get_base_config("role_info").get("party_id")
    info = {"party_name": party_name, "party_id": party_id}
    return get_json_result(retcode=0, retmsg='success', data=info)


@manager.route('/info', methods=['get'])
def client_info():
    party_name = conf_utils.get_base_config("role_info").get("party_name")
    party_id = conf_utils.get_base_config("role_info").get("party_id")
    info = {"party_name": party_name, "party_id": party_id}
    return get_json_result(retcode=0, retmsg='success', data=info)




@manager.route('/test', methods=['post'])
def test():
    request_data = request.json
    config = "/fate/examples/dsl/v1/homo_logistic_regression/test_homolr_train_job_conf.json"
    config = os.path.abspath(config)
    with open(config, 'r') as f:
        config_data = json.load(f)
    for key in request_data["algorithm_parameters"]:
        if key in config_data["algorithm_parameters"]["homo_lr_0"]:
            if isinstance(request_data["algorithm_parameters"][key], dict) and isinstance(
                    config_data["algorithm_parameters"]["homo_lr_0"][key], dict):
                for o_key in request_data["algorithm_parameters"][key]:
                    if o_key in config_data["algorithm_parameters"]["homo_lr_0"][key]:
                        config_data["algorithm_parameters"]["homo_lr_0"][key][o_key] = \
                            request_data["algorithm_parameters"][key][o_key]
            else:
                config_data["algorithm_parameters"]["homo_lr_0"][key] = request_data["algorithm_parameters"][key]
    print(config_data)


# @manager.route('/download/template', methods=['post'])
# def download_template():
#     config_data = request.json
#     file_name = config_data['file_name']
#     template_file_name = ''
#     if file_name == 'config_file':
#         template_file_name = 'test_homolr_train_job_conf.json'
#         file_full_path = os.path.join(file_utils.get_project_base_directory(), 'examples', 'dsl', 'v1',
#                                  'homo_logistic_regression', template_file_name)
#         response = make_response(
#             send_file(filename_or_fp=file_full_path, as_attachment=True))
#     if file_name == 'dsl_file':
#         template_file_name = 'test_homolr_train_job_dsl.json'
#         file_full_path = os.path.join(file_utils.get_project_base_directory(), 'examples', 'dsl', 'v1',
#                                  'homo_logistic_regression', template_file_name)
#         response = make_response(
#             send_file(filename_or_fp=file_full_path, as_attachment=True))
#     response.headers["Content-Disposition"] = "attachment; filename={};".format(template_file_name)
#     return response


def create_new_runtime_config(config_info):
    conf_dir = os.path.abspath(os.path.join(file_utils.get_project_base_directory()))
    conf_dir = os.path.join(conf_dir, "fate_flow/extension/conf/conf_file_path.json")
    with open(conf_dir, "r") as fin:
        conf_dir_dict = json.loads(fin.read())
    if not conf_dir_dict:
        if not os.path.isfile(conf_dir_dict):
            raise ValueError("config file {} dose not exist, please check!".format(conf_dir))
        raise ValueError("{} ")
    train_algorithm_name = config_info["train_algorithm_name"]
    if train_algorithm_name in conf_dir_dict:
        if config_info["isScale"]:
            dsl_path = conf_dir_dict[train_algorithm_name]["scale"]["dsl"]
            conf_path = conf_dir_dict[train_algorithm_name]["scale"]["conf"]
        else:
            dsl_path = conf_dir_dict[train_algorithm_name]["no_scale"]["dsl"]
            conf_path = conf_dir_dict[train_algorithm_name]["no_scale"]["conf"]
    else:
        raise ValueError("algorithm {} dose not exist, please check!".format(train_algorithm_name))
    conf_path = os.path.abspath(os.path.join(file_utils.get_project_base_directory(), conf_path))
    dsl_path = os.path.abspath(os.path.join(file_utils.get_project_base_directory(), dsl_path))
    with open(conf_path, "r") as fin:
        conf_dict = json.loads(fin.read())

    if not conf_dict:
        if not os.path.isfile(conf_dict):
            raise ValueError("config file {} dose not exist, please check!".format(conf_path))

        raise ValueError("{} ")

    conf_dict["initiator"]["party_id"] = int(config_info["guest"]["party_id"])
    conf_dict["job_parameters"]["common"]["work_mode"] = int(config_info["work_mode"])
    conf_dict["job_parameters"]["common"]["backend"] = 0
    conf_dict["role"]["guest"] = [int(config_info["guest"]["party_id"])]
    conf_dict["role"]["host"] = [int(item["party_id"]) for item in config_info["host"]]
    conf_dict["component_parameters"]["role"]["guest"]["0"]["reader_0"]["table"] = {
        "name": config_info["guest"]["table_name"], "namespace": "experiment"}
    if train_algorithm_name=="hetero_lr":
        conf_dict["role"]["arbiter"] = [config_info["host"][0]["party_id"]]
    pre_algorithm_name = train_algorithm_name.split('_')[0]
    for key in range(len(config_info["host"])):
        c_info = config_info["host"][key]
        if pre_algorithm_name == 'homo':
            conf_dict["component_parameters"]["role"]["host"].update({str(key): {
                "reader_0": {"table": {
                    "name": c_info["table_name"],
                    "namespace": "experiment"}
                },
                "data_split_0": {
                    "test_size": 0.01,
                    "stratified": True
                },
                "evaluation_0": {"need_run": False}
            }})
        else:
            conf_dict["component_parameters"]["role"]["host"].update({str(key): {
                "dataio_0": {"with_label": False},
                "reader_0": {"table": {
                    "name": c_info["table_name"],
                    "namespace": "experiment"}
                },
                "evaluation_0": {"need_run": False}
            }})

    conf_dict["component_parameters"]["common"]["data_split_0"]["test_size"] = float(config_info["test_size"])
    if config_info["train_algorithm_name"] == 'hetero_line':
        conf_dict["component_parameters"]["common"]["data_split_0"]["stratified"] = bool(0)
    train_algorithm_name_0 = config_info["train_algorithm_name"] + "_0"
    for key in config_info["algorithm_parameters"]:
        if key in conf_dict["component_parameters"]["common"][train_algorithm_name_0]:
            if isinstance(config_info["algorithm_parameters"][key], dict) and isinstance(
                    conf_dict["component_parameters"]["common"][train_algorithm_name_0], dict):
                for o_key in config_info["algorithm_parameters"][key]:
                    if o_key in conf_dict["component_parameters"]["common"][train_algorithm_name_0][key]:
                        conf_dict["component_parameters"]["common"][train_algorithm_name_0][key][o_key] = \
                            config_info["algorithm_parameters"][key][o_key]
            else:
                conf_dict["component_parameters"]["common"][train_algorithm_name_0][key] = \
                    config_info["algorithm_parameters"][key]

    new_config_path = gen_unique_path(config_info["train_algorithm_name"])

    with open(new_config_path, "w") as fout:
        json_str = json.dumps(conf_dict, indent=1)
        fout.write(json_str + "\n")

    return new_config_path, dsl_path

# def create_new_runtime_config_intersection(config_info):
#     conf_dir = os.path.abspath(os.path.join(file_utils.get_project_base_directory()))
#     conf_dir = os.path.join(conf_dir, "fate_flow/extension/conf/conf_file_path.json")
#     with open(conf_dir, "r") as fin:
#         conf_dir_dict = json.loads(fin.read())
#     if not conf_dir_dict:
#         if not os.path.isfile(conf_dir_dict):
#             raise ValueError("config file {} dose not exist, please check!".format(conf_dir))
#         raise ValueError("{} ")
#     else:
#         dsl_path = conf_dir_dict["intersection"]["dsl"]
#         conf_path = conf_dir_dict["intersection"]["conf"]
#     conf_path = os.path.abspath(os.path.join(file_utils.get_project_base_directory(), conf_path))
#     dsl_path = os.path.abspath(os.path.join(file_utils.get_project_base_directory(), dsl_path))
#     with open(conf_path, "r") as fin:
#         conf_dict = json.loads(fin.read())
#
#     if not conf_dict:
#         if not os.path.isfile(conf_dict):
#             raise ValueError("config file {} dose not exist, please check!".format(conf_path))
#
#         raise ValueError("{} ")
#
#     conf_dict["initiator"]["party_id"] = int(config_info["guest"]["party_id"])
#     conf_dict["job_parameters"]["common"]["work_mode"] = int(config_info["work_mode"])
#     conf_dict["job_parameters"]["common"]["backend"] = 0
#     conf_dict["role"]["guest"] = [int(config_info["guest"]["party_id"])]
#     conf_dict["role"]["host"] = [int(item["party_id"]) for item in config_info["host"]]
#     conf_dict["component_parameters"]["role"]["guest"]["0"]["reader_0"]["table"] = {
#         "name": config_info["guest"]["table_name"], "namespace": "experiment"}
#
#     for key in range(len(config_info["host"])):
#         c_info = config_info["host"][key]
#         conf_dict["component_parameters"]["role"]["host"].update({str(key): {
#             "dataio_0": {"with_label": False},
#             "reader_0": {"table": {
#                 "name": c_info["table_name"],
#                 "namespace": "experiment"}
#             },
#             "evaluation_0": {"need_run": False}
#         }})
#
#     new_config_path = gen_unique_path(config_info["guest"]["table_name"])
#
#     with open(new_config_path, "w") as fout:
#         json_str = json.dumps(conf_dict, indent=1)
#         fout.write(json_str + "\n")
#
#     return new_config_path, dsl_path

def exec_task(config_path, dsl_path):
    subp = subprocess.Popen(["python",
                             fate_flow_path,
                             "-f",
                             "submit_job",
                             "-d",
                             dsl_path,
                             "-c",
                             config_path],
                            shell=False,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)

    stdout, stderr = subp.communicate()
    stdout = stdout.decode("utf-8")
    print("stdout:" + str(stdout))

    status = -1
    try:
        stdout = json.loads(stdout)
        status = stdout["retcode"]
    except:
        raise ValueError("failed to exec task, stderr is {}, stdout is {}".format(stderr, stdout))

    if status != 0:
        raise ValueError(
            "failed to exec task, status:{}, stderr is {} stdout:{}".format(status, stderr, stdout))

    jobid = stdout["jobId"]
    return jobid


def gen_unique_path(train_name):
    str_time = str(int(time.time()))
    config_file_name = 'config_' + str_time + '.json'
    filename = os.path.join(file_utils.get_project_base_directory(), 'data', 'upload', train_name)
    config_file_path = os.path.join(filename, config_file_name)
    os.makedirs(os.path.dirname(config_file_path), exist_ok=True)
    return config_file_path

