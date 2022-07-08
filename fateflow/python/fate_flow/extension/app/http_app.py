import json
import os

from flask import Flask, request, jsonify

from fate_flow.settings import stat_logger
from fate_flow.extension.utils import predict_file_utils


# @manager.route('/adapter/getFeature', methods=['post'])
# def get_feature():
    # request_data = request.json
    # data = json.dumps(request_data)
    # stat_logger.info(f"-------------FATE Flow log{data}")
    # print(data)
    #data = {'x0': 0.449512, 'x1': -1.247226, 'x2': 0.413178, 'x3': 0.303781, 'x4': -0.123848, 'x5': -0.184227, 'x6': -0.219076, 'x7': 0.268537, 'x8': 0.015996, 'x9': -0.789267, 'x10': -0.33736, 'x11': -0.728193, 'x12': -0.442587, 'x13': -0.272757, 'x14': -0.608018, 'x15': -0.577235, 'x16': -0.501126, 'x17': 0.143371, 'x18': -0.466431, 'x19': -0.554102}
    # data = {}
    # res_data = {}
    # res_data["code"] = 200
    # res_data["data"] = data
    # return jsonify(res_data)

# @manager.route('/adapter/getFeature', methods=['post'])
# def get_feature():
#     request_data = request.json
#     res_data = {}
#     data = {}
#     res_data["code"] = 200
#     res_data["data"] = {'x0': float(0.449512)}
#     data["id"] = request_data["id"]
#     data["model_version"] = request_data["model_version"]
#     res_data["data"] = data
#     return jsonify(res_data)


@manager.route('/adapter/getFeature', methods=['post'])
def get_feature():
    request_data = request.json
    service_id = int(request_data["service_id"])
    predict_file = predict_file_utils.select_by_service_id(service_id)
    predict_file_path = predict_file.f_data_path
    with open(os.path.join(predict_file_path)) as f:
        s = f.read()
        f.close()
    data = {"file_string": str(s)}
    stat_logger.info(f"-------------FATE Flow log{data}")
    res_data = {"code": 200, "data": data}
    return jsonify(res_data)