import json
import os
import shutil
import sys
import time

import requests
from flask import jsonify
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
from sklearn import preprocessing
from sklearn.preprocessing import OneHotEncoder

from fate_arch.common import file_utils, conf_utils
from fate_flow.db.db_models import DB, Job
from fate_flow.settings import FATE_FLOW_SERVICE_NAME, API_VERSION
import pandas as pd


@DB.connection_context()
def select_data_list(data_type):
    jobs = Job.select(Job.f_job_id, Job.f_create_date, Job.f_create_time,Job.f_runtime_conf, Job.f_initiator_role, Job.f_status).where(Job.f_initiator_role == 'local', Job.f_status == 'success').order_by(Job.f_create_time.desc())
    data_list = []
    for job in jobs:
        data_info = job.f_runtime_conf["component_parameters"]["role"]["local"]["0"]["upload_0"]
        if int(data_info.setdefault("data_type", 0)) == int(data_type):
            data_info["create_time"] = job.f_create_time
            data_info["job_id"] = job.f_job_id
            # data_info["work_mode"] = job.f_work_mode
            if data_info.setdefault("custom_table", "") != "":
                data_info["custom_table"] = json.loads(data_info["custom_table"])
            data_list.append(data_info)
    return data_list


@DB.connection_context()
def data_detail(job_id):
    job = Job.select().where(Job.f_job_id == job_id).get()
    data_info = job.f_runtime_conf["component_parameters"]["role"]["local"]["0"]["upload_0"]
    if data_info.setdefault("custom_table", "") != "":
        data_info["custom_table"] = json.loads(data_info["custom_table"])
    return data_info


@DB.connection_context()
def job_path(job_id):
    job = Job.select().where(Job.f_job_id == job_id).get()
    job_file_path = os.path.join(file_utils.get_project_base_directory(), 'jobs', job.f_job_id)
    return job_file_path


@DB.connection_context()
def delete_data(job_id):
    job = Job.select().where(Job.f_job_id == job_id).get()
    row = job.delete_instance()
    return row


def data_upload(data_info):
    ip = conf_utils.get_base_config(FATE_FLOW_SERVICE_NAME).get("host")
    http_port = conf_utils.get_base_config(FATE_FLOW_SERVICE_NAME).get("http_port")
    server_url = "http://{}:{}/{}".format(ip, http_port, API_VERSION)

    config_data = {'table_name': data_info["table_name"], 'namespace': "experiment",
                   'data_type': 1, 'description': data_info["description"],
                   'work_mode': data_info["work_mode"], 'head': 1, 'partition': 16, 'custom_table': data_info["label_info"], 'history_table_name': data_info["history_table_name"]}
    file_name = os.path.join(data_info["file_path"])
    os.makedirs(os.path.dirname(file_name), exist_ok=True)
    config_data['file'] = file_name
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
    return response


# one-hot
class LocalOneHotEncoder(object):

  def __init__(self, target_columns):
    self.enc = OneHotEncoder(handle_unknown='ignore')
    self.col_names = target_columns

  def fit(self, df):
      le=preprocessing.LabelEncoder()
      for i in self.col_names:
        df[i] = le.fit_transform(df[i])
      self.enc.fit(df[self.col_names].values)
      self.new_col_names = self.gen_col_names(df)
  #表头
  def gen_col_names(self, df):
    new_col_names = []
    for col in self.col_names:
      for val in df[col].unique():
        new_col_names.append("{}_{}".format(col, val))
    return new_col_names

  def transform(self, df):
     return pd.DataFrame(data = self.enc.transform(df[self.col_names]).toarray(),
                         columns = self.new_col_names,
                         dtype=int)


def onehot_info(file_path, index_info):
    train_data = pd.read_csv(file_path)
    train_data = pd.DataFrame(train_data)
    onehot_columms = []
    # 记录有几个字段需要onehot处理，如果没有不走LocalOneHotEncoder函数
    onehot_count = 0
    for i in index_info:
        if not i["is_use"]:
            train_data = train_data.drop(columns=i["label"])
        else:
            if i["type"] == 2:
                onehot_count += 1
                onehot_columms.append(i["label"])
                i["content"] = "map处理"
    if onehot_count !=  0:
        local_ohe = LocalOneHotEncoder(onehot_columms)
        local_ohe.fit(train_data)
        oht_df = local_ohe.transform(train_data)
        df = pd.concat([train_data, oht_df], axis=1)
        for i in onehot_columms:
            df = df.drop(columns=i)
        return df, index_info
    else:
        return train_data, index_info



def onehot_use(file_path,label_info):
    m, label_info = onehot_info(file_path, label_info)
    dir_name = os.path.join(file_utils.get_project_base_directory(), 'data', 'upload', 'preprocess')
    os.makedirs(dir_name, exist_ok=True)
    str_time = str(int(time.time()))
    file_path = os.path.join(dir_name, str_time + ".csv")
    m.to_csv(file_path, index=False)
    return file_path, label_info

