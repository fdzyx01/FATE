import time

from flask import Flask, request, jsonify, g, current_app

from fate_flow.extension.exception.error_code import Success
from fate_flow.extension.utils import user_utils
from fate_flow.extension.utils.user_utils import *
from fate_flow.utils.api_utils import get_json_result
from fate_flow.extension.model.user import UserForm, LoginForm

# manager.config["JWT_SECRET"] = "FATE1.5"
# manager.config["JWT_EXPIRY_HOURS"] = 2 * 3600
# manager.config["JWT_EXPIRY_HOURS"] = 120
# manager.config["JWT_REFRESH_DAYS"] = 15 * 24 * 3600



@manager.route('/login', methods=['post'])
def login():
    form = LoginForm().validate_for_api()
    account = form.account.data
    pwd = form.pwd.data
    response = verity(account, pwd)
    return get_json_result(retcode=0, retmsg='登录成功', data=response)


@manager.route('/register', methods=['post'])
def register():
    form = UserForm().validate_for_api()
    account = form.account.data
    pwd = form.pwd.data
    nickname = form.nickname.data
    party_id = form.party_id.data
    str_time = str(int(time.time()))
    add_user(account, pwd, nickname, party_id, str_time)
    return Success()

@manager.route('/find', methods=['post'])
def find_user():
    request_data = request.json
    id = request_data["id"]
    data = user_utils.select_user(id)
    return get_json_result(retcode=0, retmsg='success', data=data)

@manager.route('/update/info', methods=['post'])
def update_info():
    request_data = request.json
    id = request_data["id"]
    account = request_data["account"]
    nickname = request_data["nickname"]
    str_time = str(int(time.time()))
    data = user_utils.update_info(id, account, nickname, str_time)
    return get_json_result(retcode=0, retmsg='success', data=data)

@manager.route('/update/pwd', methods=['post'])
def update_pwd():
    request_data = request.json
    id = request_data["id"]
    old_pwd = request_data["old_pwd"]
    new_pwd = request_data["new_pwd"]
    response = verity_pwd(id, old_pwd)
    if response["retcode"]==0:
        str_time = str(int(time.time()))
        data = user_utils.update_user_pwd(id, str_time, new_pwd)
    return get_json_result(retcode=0, retmsg='success')

