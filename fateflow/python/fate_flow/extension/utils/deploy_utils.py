import operator

import requests
from fate_arch.common import conf_utils
from fate_flow.operation.job_saver import str_to_time_stamp
from fate_flow.utils.api_utils import federated_api
from fate_flow.utils.api_utils import get_json_result
from fate_flow.extension.model.db_models import DB, Deploy
from fate_flow.settings import FATE_FLOW_SERVICE_NAME, API_VERSION


ip = conf_utils.get_base_config(FATE_FLOW_SERVICE_NAME).get("host")
http_port = conf_utils.get_base_config(FATE_FLOW_SERVICE_NAME).get("http_port")


@DB.connection_context()
def select_count():
    count = Deploy.select().count()
    return count


@DB.connection_context()
def insert_deploy(service_id, location, status, msg, str_time, model_id, context):
    data = Deploy.create(f_service_id=service_id, f_status=status, f_location=location, f_msg=msg, f_model_id=model_id,
                         f_context=context, f_create_time=str_time)

@DB.connection_context()
def select_by_server_id(service_id):
    try:
        deploy = Deploy.select().where(Deploy.f_service_id == service_id).get()
    except:
        response = {
            "retcode": 1,
            "retmsg": "no server_id could be found"
        }
        return response
    data_info = {}
    data_info["f_id"] = deploy.f_id
    data_info["f_service_id"] = deploy.f_service_id
    data_info["f_msg"] = deploy.f_msg
    data_info["f_create_time"] = deploy.f_create_time
    data_info["f_status"] = deploy.f_status
    data_info["f_context"] = deploy.f_context
    data_info["f_model_id"] = deploy.f_model_id
    response = {
        "retcode": 0,
        "retmsg": "success",
        "data": data_info
    }
    return response


@DB.connection_context()
def select_by_id(id):
    # deploy = Deploy.select().where(Deploy.f_id == id).get()
    try:
        deploy = Deploy.get_by_id(id)
    except:
        response = {
            "retcode": 1,
            "retmsg": "no id could be found"
        }
        return response
    data_info = {}
    data_info["f_id"] = deploy.f_id
    data_info["f_service_id"] = deploy.f_service_id
    data_info["f_msg"] = deploy.f_msg
    data_info["f_create_time"] = deploy.f_create_time
    data_info["f_status"] = deploy.f_status
    data_info["f_context"] = deploy.f_context
    data_info["f_model_id"] = deploy.f_model_id
    response = {
        "retcode": 0,
        "retmsg": "success",
        "data": data_info
    }
    return response


@DB.connection_context()
def delete_deploy(id):
    Deploy.delete().where(Deploy.f_id == id).execute()
    # row = Deploy.delete().where(Deploy.f_id == id).execute()
    # return row


@DB.connection_context()
def del_by_service_id(service_id):
    Deploy.delete().where(Deploy.f_service_id == service_id).execute()


@DB.connection_context()
def select_by_list(page, page_length):
    deploys = Deploy.select().order_by(Deploy.f_create_time.desc()).paginate(int(page), int(page_length))
    deploy_list = []
    for deploy in deploys:
        data_info = {}
        data_info["f_id"] = deploy.f_id
        data_info["f_service_id"] = deploy.f_service_id
        data_info["f_msg"] = deploy.f_msg
        data_info["f_create_time"] = deploy.f_create_time
        data_info["f_status"] = deploy.f_status
        data_info["f_context"] = deploy.f_context
        data_info["f_model_id"] = deploy.f_model_id
        deploy_list.append(data_info)
    return deploy_list


def grpc_deploy_command(job_id, method, job_info, json_body, endpoint):
    src_party_id = job_info["initiator"]["party_id"]
    src_role = job_info["initiator"]["role"]
    federated_response = {}
    federated_response["host"] = {}
    federated_response["retcode"] = 104
    federated_response["retmsg"] = "One of the host execution errors."
    flag = True
    for dest_party_id in job_info["role"]["host"]:
        try:
            response = federated_api(job_id=job_id,
                                     method=method,
                                     endpoint=endpoint,
                                     src_party_id=src_party_id,
                                     dest_party_id=dest_party_id,
                                     src_role=src_role,
                                     json_body=json_body,
                                     federated_mode="MULTIPLE")
            federated_response["host"][dest_party_id] = response
            if response["retcode"] != 0: flag = False
        except Exception as e:
            federated_response["host"][dest_party_id] = {
                "retcode": 104,
                "retmsg": "Federated schedule error, {}".format(e)
            }
            flag = False
    if flag:
        federated_response["retcode"] = 0
        federated_response["retmsg"] = "success"
    return federated_response


def find_job_info(id):
    url = "http://{}:{}/{}".format(ip, http_port, API_VERSION)
    response = select_by_id(id)
    if response["retcode"]!=0:
        return response

    data = {"job_id": response["data"]["f_model_id"], "service_id": response["data"]["f_service_id"]}
    response = requests.post("/".join([url, "job", "query"]), json=data)
    job_info = response.json()
    if len(job_info["data"]) == 0:
        return {"retcode": 1, "retmsg": 'no job could be found'}

    info = {
        "initiator": {},
        "role": {},
        "job_id": data["job_id"],
        "service_id": data["service_id"]
    }
    info["initiator"]["party_id"] = job_info["data"][0]["f_party_id"]
    info["initiator"]["role"] = "host"
    if job_info["data"][0]["f_party_id"] == job_info["data"][0]["f_initiator_party_id"]:
        info["initiator"]["role"] = "guest"
    info["role"]["guest"] = [str(i) for i in job_info["data"][0]["f_roles"]["guest"]]
    info["role"]["host"] = [str(i) for i in job_info["data"][0]["f_roles"]["host"]]
    return {"retcode": 0, "data": info}


@DB.connection_context()
def update_status(service_id, status):
    Deploy.update({Deploy.f_status: status}).where(Deploy.f_service_id == service_id).execute()

@DB.connection_context()
def select_deploy_list(status):
    deploys = Deploy.select().order_by(Deploy.f_create_time.desc()).where(Deploy.f_status==status)
    deploy_list = []
    for deploy in deploys:
        data_info = {}
        data_info["f_id"] = deploy.f_id
        data_info["f_service_id"] = deploy.f_service_id
        data_info["f_msg"] = deploy.f_msg
        data_info["f_create_time"] = deploy.f_create_time
        data_info["f_status"] = deploy.f_status
        data_info["f_context"] = deploy.f_context
        data_info["f_model_id"] = deploy.f_model_id
        deploy_list.append(data_info)
    return deploy_list

@DB.connection_context()
def query_deploy(reverse=None, order_by=None, **kwargs):
    filters = []
    for f_n, f_v in kwargs.items():
        attr_name = 'f_%s' % f_n
        if attr_name in ['f_start_time', 'f_end_time', 'f_elapsed'] and isinstance(f_v, list):
            if attr_name == 'f_elapsed':
                b_timestamp = f_v[0]
                e_timestamp = f_v[1]
            else:
                # time type: %Y-%m-%d %H:%M:%S
                b_timestamp = str_to_time_stamp(f_v[0]) if isinstance(f_v[0], str) else f_v[0]
                e_timestamp = str_to_time_stamp(f_v[1]) if isinstance(f_v[1], str) else f_v[1]
            filters.append(getattr(Deploy, attr_name).between(b_timestamp, e_timestamp))
        elif hasattr(Deploy, attr_name):
            if f_v=="":
                continue
            else:
                if isinstance(f_v, set):
                    filters.append(operator.attrgetter('f_%s' % f_n)(Deploy) << f_v)
                else:
                    filters.append(operator.attrgetter('f_%s' % f_n)(Deploy) == f_v)
    if len(filters)==0:
        deploys = Deploy.select().order_by(Deploy.f_create_time.desc())
    else:
        deploys = Deploy.select().where(*filters).order_by(Deploy.f_create_time.desc())
        if reverse is not None:
            if not order_by or not hasattr(Deploy, f"f_{order_by}"):
                order_by = "create_time"
            if reverse is True:
                deploys = deploys.order_by(getattr(Deploy, f"f_{order_by}").desc())
            elif reverse is False:
                deploys = deploys.order_by(getattr(Deploy, f"f_{order_by}").asc())
    list = [deploy for deploy in deploys]
    page = kwargs.pop('page')
    page_length = kwargs.get('page_length')
    deploy_list = paginate_data(int(page), int(page_length), list)
    count = len(list)
    return deploy_list, page, page_length, count

def paginate_data(page_num, per_page_data,inter_list):
    view_data = []
    view_data_count = 0
    stat_index = (page_num - 1) * per_page_data
    end_index = page_num * per_page_data
    for inter in inter_list:
        if stat_index <= view_data_count < end_index:
            view_data.append(inter)
        if view_data_count >= end_index:
            break
        view_data_count += 1
    return view_data
