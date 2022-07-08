import json
import os
import subprocess
import time


from flask import Flask, request, jsonify, g

from fate_arch.common import conf_utils
from fate_flow.extension.common import file_utils
from fate_flow.extension.utils.user_utils import verify_jwt
from fate_flow.settings import stat_logger
from fate_flow.extension.utils import job_utils, intersection_job_utils
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

@manager.route('/submit/job/intersection', methods=['post'])
def submit_job_general_intersection():
    request_data = request.json
    conf_path, dsl_path = create_new_runtime_config_intersection(request_data)
    job_id = exec_task(conf_path, dsl_path)
    data = {"job_id": job_id}
    job_name = request_data["job_name"]
    job_description = request_data["job_description"]
    date = intersection_job_utils.insert_job(job_description=job_description, job_name=job_name, job_id=job_id)
    return get_json_result(retcode=0, retmsg='success', data=data)


@manager.route('/list/job/intersection', methods=['POST'])
def list_job_intersection():
    request_data = request.json
    page = int(request_data.get('page', 1))
    page_length = int(request_data.get('page_length', 10))
    jobs= intersection_job_utils.list_job_intersection(page,page_length)
    count=intersection_job_utils.list_job_intersection_count()
    if not jobs:
        return get_json_result(retcode=101, retmsg='No job found')
    # return get_json_result(retcode=0, retmsg='success', data=[job.to_json() for job in jobs],count=len(jobs))
    return jsonify({
        'retcode': 0,
        'retmsg': 'success',
        'page': page,
        'page_length': page_length,
        'data': [job.to_json() for job in jobs],
        'count': count
    })

def create_new_runtime_config_intersection(config_info):
    conf_dir = os.path.abspath(os.path.join(file_utils.get_project_base_directory()))
    conf_dir = os.path.join(conf_dir, "fate_flow/extension/conf/conf_file_path.json")
    with open(conf_dir, "r") as fin:
        conf_dir_dict = json.loads(fin.read())
    if not conf_dir_dict:
        if not os.path.isfile(conf_dir_dict):
            raise ValueError("config file {} dose not exist, please check!".format(conf_dir))
        raise ValueError("{} ")
    else:
        dsl_path = conf_dir_dict["intersection"]["dsl"]
        conf_path = conf_dir_dict["intersection"]["conf"]
    conf_path = os.path.abspath(os.path.join(file_utils.get_project_base_directory(), conf_path))
    dsl_path = os.path.abspath(os.path.join(file_utils.get_project_base_directory(), dsl_path))
    with open(conf_path, "r") as fin:
        conf_dict = json.loads(fin.read())

    if not conf_dict:
        if not os.path.isfile(conf_dict):
            raise ValueError("config file {} dose not exist, please check!".format(conf_path))

        raise ValueError("{} ")

    conf_dict["initiator"]["party_id"] = int(config_info["guest"]["party_id"])
    conf_dict["job_parameters"]["common"]["work_mode"] = 1
    conf_dict["job_parameters"]["common"]["backend"] = 0
    conf_dict["role"]["guest"] = [int(config_info["guest"]["party_id"])]
    conf_dict["role"]["host"] = [int(item["party_id"]) for item in config_info["host"]]
    conf_dict["component_parameters"]["role"]["guest"]["0"]["reader_0"]["table"] = {
        "name": config_info["guest"]["table_name"], "namespace": "experiment"}

    for key in range(len(config_info["host"])):
        c_info = config_info["host"][key]
        conf_dict["component_parameters"]["role"]["host"].update({str(key): {
            "dataio_0": {"with_label": False},
            "reader_0": {"table": {
                "name": c_info["table_name"],
                "namespace": "experiment"}
            },
            "evaluation_0": {"need_run": False}
        }})

    new_config_path = gen_unique_path(config_info["guest"]["table_name"])

    with open(new_config_path, "w") as fout:
        json_str = json.dumps(conf_dict, indent=1)
        fout.write(json_str + "\n")

    return new_config_path, dsl_path

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