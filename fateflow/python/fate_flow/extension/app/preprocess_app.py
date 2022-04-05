import json
import math
import os
import shutil
import pydotplus
import time

from flask import Flask, jsonify, request, make_response, send_from_directory, g
from six import StringIO
from sklearn.cluster import KMeans
import pandas as pd
import numpy as np
from collections import Counter

from sklearn.tree import DecisionTreeClassifier
from sklearn.tree import export_graphviz

from fate_arch import storage
from fate_flow.extension.common import file_utils
from fate_flow.settings import stat_logger
from fate_flow.extension.utils import preprocess_util
from fate_flow.utils.api_utils import get_json_result


@manager.errorhandler(500)
def internal_server_error(e):
    stat_logger.exception(e)
    return get_json_result(retcode=100, retmsg=str(e))


@manager.route('/test')
def test():
    response = {'test':'hello word'}
    return jsonify(response)


@manager.route('/data/list')
def select_data_list():
    data_type = request.args.get("data_type")
    data_list = preprocess_util.select_data_list(int(data_type))
    if not data_list:
        return get_json_result(retcode=101, retmsg='No data_list found')
    return get_json_result(retcode=0, retmsg='success', data=data_list)


@manager.route('/data/find', methods=['POST'])
def find_data():
    job_id = request.form['job_id']
    data= preprocess_util.data_detail(job_id)
    return get_json_result(retcode=0, retmsg='success', data=data)

@manager.route('/data_find', methods=['POST'])
def find_pre_data():
    file_path = request.json['file_path']
    data = pd.read_csv(file_path)
    result_dict = {}
    result_dict['all_num'] = len(data)
    df = np.array(data.iloc[:100]).tolist()  # 取前100个样本
    df.insert(0, list(data.columns))  # 插入表头
    result_dict['data'] = df
    return get_json_result(retcode=0, retmsg='success', data=result_dict)


@manager.route('/data/del', methods=['POST'])
def data_del():
    job_id = request.form['job_id']
    job_file_path = preprocess_util.job_path(job_id)
    data_info = preprocess_util.data_detail(job_id)
    data_table_meta = storage.StorageTableMeta(name=data_info["name"], namespace=data_info["namespace"])
    if data_table_meta:
            data_table_meta.destroy_metas()
    row = preprocess_util.delete_data(job_id)
    if row != 0:
        try:
            shutil.rmtree(job_file_path)
        except:
             raise Exception('remove job file failed')
    return get_json_result(retcode=0, retmsg='success')


@manager.route('/data/preprocess', methods=['POST'])
def data_preprocess():
    request_data = request.json
    file_path = request_data["file_path"]
    label_info = request_data["label_info"]
    new_file_path, onehot_label_info = preprocess_util.onehot_use(file_path, label_info)
    request_data["label_info"] = json.dumps(onehot_label_info)
    request_data["file_path"] = new_file_path
    response = preprocess_util.data_upload(request_data)
    return get_json_result(retcode=response["retcode"], retmsg=response["retmsg"])

@manager.route('/data/hist', methods=['POST'])
def data_hist():
    request_data = request.json
    file_path = request_data["file_path"]
    feature = request_data["feature"]
    n_count = len(feature)
    # excel是输入的表
    excel = pd.read_csv(file_path)
    article_info = {}
    # reg为最外面的
    reg = json.loads(json.dumps(article_info))
    reg["count"] = n_count
    reg["data"] = []
    for feat in feature:
        data1 = json.loads(json.dumps(article_info))
        data1["title"] = feat + "的直方图"  # 属性
        data1["sub"] = []
        data1["series"] = []
        dic = Counter(excel[feat])  # 归类feat的类型
        f = zip(dic.keys(), dic.values())
        f = sorted(f)
        columns = [i[0] for i in f]
        _y = [i[1] for i in f]
        if len(columns) >= 10:  # columns类型大于10就合并
            diff = (columns[-1] - columns[0]) / 10  # 将数据大小分为10份
            new_y = []
            temp = columns[0]
            for num in range(10):
                y_s = 0
                for i, j in enumerate(columns):
                    if (j > temp) and (j <= temp + diff):
                        y_s += _y[i]
                temp += diff
                data1["sub"].append(round(temp, 3))  # 保留小数点后3位
                new_y.append(y_s)
        else:
            data1["sub"] = columns
        _y = new_y
        data1["series"].append({"name": feat + "_hist", "data": _y, "max": math.ceil(max(_y) * 1.1)})  # max增加10%以提高美观
        # 以下为正态分布的求
        std = excel[feat].std()
        mean = excel[feat].mean()
        x = np.linspace(min(excel[feat]), max(excel[feat]), len(data1["sub"]))
        y_sig = np.exp(-(x - mean) ** 2 / (2 * std ** 2) / (math.sqrt(2 * math.pi) * std))  # y_sig得出来一个列表
        data1["series"].append(
            {"name": feat + "_line", "data": y_sig.tolist(), "max": 1.1})  # 设置为1.1的目的是y_sig中最大值只能接近1不能超过1
        reg["data"].append(data1)
    return get_json_result(retcode=0, retmsg='success', data=reg)

@manager.route('/data/heatmap', methods=['POST'])
def data_heatmap():
    request_data = request.json
    file_path = request_data["file_path"]
    feature = request_data["feature"]
    excel = pd.read_csv(file_path)
    excel = excel[feature]
    article_info = {}
    js = json.loads(json.dumps(article_info))
    columns = list(excel.columns)
    df = excel.corr(method ='pearson')
    _list = []
    for i in range(len(columns)):
        for j in range(len(columns)):
            _list.append([i,j,round(df.iloc[i,j],3)])
    js["data"] = _list
    js["titleLeft"] = columns
    js["titleBottom"] = columns
    return get_json_result(retcode=0, retmsg='success', data=js)

@manager.route('/data/dotmap', methods=['POST'])
def data_dotmap():
    request_data = request.json
    file_path = request_data["file_path"]
    y_feat = request_data["y_feat"]
    x_feat = request_data["x_feat"]
    n_count = len(x_feat)
    excel = pd.read_csv(file_path)
    article_info = {}
    reg = json.loads(json.dumps(article_info))
    reg["count"] = n_count
    reg["data"] = []
    # 每个X_feat做X轴
    for x_fe in x_feat:
        data = json.loads(json.dumps(article_info))
        data["title"] = y_feat+"与"+x_fe + "的散点图"
        data["x"] = x_fe
        data["y"] = y_feat
        data["series"] = []
        x_list = list(excel[x_fe])
        y_list = list(excel[y_feat])
        daf = []
        for i, j in zip(x_list, y_list):
            daf.append([i, j])
        data["series"].append({"name": x_fe, "data": daf})
        reg["data"].append(data)
    return get_json_result(retcode=0, retmsg='success', data=reg)

@manager.route('/data/cluster_data', methods=['POST'])
def cluster_data():
    request_data = request.json
    file_path = request_data["file_path"]
    feature = request_data["feature"]
    n = int(request_data["n"])
    # read data and transfrom to nparray
    data = pd.read_csv(file_path)
    X = np.array(data)
    a = data.columns.get_loc(feature[0])
    b = data.columns.get_loc(feature[1])
    # structer kmeans
    estimator = KMeans(n_clusters=n)  # 构造聚类器
    estimator.fit(X)  # 聚类
    label_pred = estimator.labels_
    centers = estimator.cluster_centers_
    # 储存分类后的data
    label_pred_1 = pd.DataFrame(label_pred)
    data = data.join(label_pred_1)
    data.to_csv('data.csv')
    # create json
    article_info = {}
    data_json = json.loads(json.dumps(article_info))
    data_json["title"] = "main title"
    data_json["subTitle"] = "half title"
    data_json["legend"] = {"data": []}
    data_json["series"] = []
    # 输出质心
    df = pd.DataFrame(centers)
    df = df[[a, b]]
    df = np.array(df)
    _list = df.tolist()
    data_json["legend"]["data"].append(_list)
    # 输出每一个类别的样本点
    for i in range(n):
        df = pd.DataFrame(X[label_pred == i])
        df = df[[a, b]]
        df = np.array(df)
        _list = df.tolist()
        data_json["series"].append({"name": i, "data": _list})
    data_json["chart"] = data_json["series"]
    data_json["info"] = data[0].tolist()
    return get_json_result(retcode=0, retmsg='success', data=data_json)

@manager.route('/data/d_tree', methods=['post'])
def d_tree():
    request_data = request.json
    file_path = request_data["file_path"]
    feature = request_data["feature"]
    n = int(request_data["n"])
    y_feature= request_data["y_feature"]
    # read data and transfrom to nparray
    data = pd.read_csv(file_path)
    X = data[feature]
    Y = data[y_feature]
    X_np = np.array(X)
    Y_np = np.array(Y)

    clf = DecisionTreeClassifier(max_depth=n)
    clf.fit(X_np, Y_np)

    dot_data = StringIO()  # 把文件暂时写在内存的对象中

    export_graphviz(
        clf,
        out_file=dot_data,
        feature_names=X.columns,
        filled=True, rounded=True, special_characters=True
    )

    # print("Sklearn verion is {}".format(sklearn.__version__))
    dir_name = os.path.join(file_utils.get_project_base_directory(), 'data', 'upload')
    str_time = str(int(time.time()))
    file_path = 'upload_img' + str_time
    file_name = os.path.join(dir_name, file_path)
    os.makedirs(os.path.dirname(dir_name), exist_ok=True)
    graph = pydotplus.graph_from_dot_data(dot_data.getvalue())
    graph.write_png(file_name+'.png')
    image_data = open(file_name + ".png", "rb").read()
    response = make_response(image_data)
    response.headers['Content-Type'] = 'image/png'
    return response
