from fate_flow.extension.exception.error import APIException


class ParameterException(APIException):
    code = 400
    msg = 'invalid parameter'
    error_code = 1000


class Success(APIException):
    code = 201
    msg = 'Success'
    error_code = 0


class AuthFailed(APIException):
    code = 401
    error_code = 1008
    msg = 'authorization failed'


class ServerError(APIException):
    code = 500
    msg = 'sorry, we made a mistake (*￣︶￣)!'
    error_code = 999