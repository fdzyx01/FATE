# 需要 PyJWT
import functools
import jwt
from datetime import datetime, timedelta

from flask import current_app, g, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from fate_flow.extension.model.db_models import DB, User
from fate_flow.utils.api_utils import get_json_result
from fate_flow.extension.exception.error_code import ParameterException, ServerError


def verify_jwt(token, secret=None):
    """
    检验jwt
    :param token: jwt
    :param secret: 密钥
    :return: dict: payload
    """
    if not secret:
        secret = current_app.config['JWT_SECRET']
    try:
        payload = jwt.decode(token, secret, algorithms=['HS256'])
        code = 0
    except jwt.InvalidTokenError:
        payload = None
        code = 402
    except jwt.PyJWTError:
        payload = None
        code = 401
    return payload, code


def generate_jwt(payload, expiry, secret=None):
    """
    生成jwt
    :param payload: dict 载荷
    :param expiry: datetime 有效期
    :param secret: 密钥
    :return: jwt
    """
    _payload = {'exp': expiry}
    _payload.update(payload)

    if not secret:
        secret = current_app.config['JWT_SECRET']

    token = jwt.encode(_payload, secret, algorithm='HS256')
    return token


def login_required(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if not g.user_id:
            return get_json_result(retcode=401, retmsg='User must be authorized.')
        else:
            return f(*args, **kwargs)
    return wrapper


def generate_token(user_id, nickname, need_refresh_token=True):
    """
    生成token 和refresh_token
    :param user_id: 用户id
    :return: token2小时, refresh_token14天
    """
    '生成时间信息'
    current_time = datetime.utcnow()
    '指定有效期  业务token -- 2小时'
    expire_time = current_time + timedelta(seconds=current_app.config['JWT_EXPIRY_HOURS'])
    token = generate_jwt({'user_id': user_id, "nickname": nickname}, expiry=expire_time)
    return token


def check_password(self, raw):
    if not self:
        return False
    return check_password_hash(self, raw)


@DB.connection_context()
def select_one(account):
    try:
        find = User.select().where(User.f_account == account).get()
        return find
    except:
        return False

@DB.connection_context()
def select_by_id(id):
    try:
        find = User.select().where(User.id == id).get()
        return find
    except:
        return False

@DB.connection_context()
def select_user(id):
    user = User.get_by_id(id)
    data_info = {}
    data_info["f_account"] = user.f_account
    data_info["f_nickname"] = user.f_nickname
    data_info["f_party_id"] = user.f_party_id
    data_info["f_create_time"] = user.f_create_time
    return data_info

@DB.connection_context()
def update_info(id, account, nickname, str_time):
    User.update({User.f_account: account, User.f_create_time: str_time, User.f_nickname: nickname}).where(User.id == id).execute()

@DB.connection_context()
def verity(account, password):
    find = select_one(account)
    if not find:
        raise ParameterException(msg='用户不存在')
    if not check_password(find.f_pwd, password):
        raise ParameterException(msg='密码错误')
    return {"id": find.id, "nickname": find.f_nickname, "account": find.f_account}

@DB.connection_context()
def verity_pwd(id,password):
    find = select_by_id(id)
    if not find:
        raise ParameterException(msg='用户不存在')
    if not check_password(find.f_pwd, password):
        raise ParameterException(msg='旧密码错误')
    return {"retcode": 0, "retmsg": 'success'}

@DB.connection_context()
def update_user_pwd(id, str_time, new_pwd):
    User.update({User.f_create_time: str_time, User.f_pwd: generate_password_hash(new_pwd)}).where(User.id == id).execute()

@DB.connection_context()
def add_user(account, pwd, nickname, party_id, str_time):
    if select_one(account):
        raise ParameterException(msg="Duplicate account")
    try:
        data = User.create(f_account=account, f_pwd=generate_password_hash(pwd), f_nickname=nickname, f_party_id=party_id, f_create_time=str_time)
    except:
        raise ServerError(msg="Storage failed")

