from fate_flow.extension.model.base import BaseForm
# 需要 pip install wtforms
from wtforms import StringField, IntegerField
from wtforms.validators import DataRequired, length, Regexp, EqualTo, Optional


class UserForm(BaseForm):
    account = StringField(validators=[DataRequired(message='The value is not allowed to be empty'), length(
        min=4, max=50
    )])
    pwd = StringField(validators=[
        DataRequired(message='The value is not allowed to be empty'),
        Regexp(r'^[A-Za-z0-9_*&$#@]{6,22}$'),
        EqualTo('confirm', message='Passwords must match')
    ])
    confirm = StringField(validators=[
        DataRequired(message='The value is not allowed to be empty'),
        Regexp(r'^[A-Za-z0-9_*&$#@]{6,22}$')
    ])
    nickname = StringField(validators=[
        DataRequired(),
        length(min=2, max=30)
    ])
    party_id = StringField(validators=[
        DataRequired(),
        length(min=2, max=30)
    ])
    email = StringField(validators=[
        Optional(strip_whitespace=True),
        Regexp(r'^[A-Za-z0-9\u4e00-\u9fa5]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$', message='invalidate email')
    ])
    phone = StringField(validators=[
        Regexp(r'^[0-9]{3,22}$'),
        Optional(strip_whitespace=True)
    ])


class LoginForm(BaseForm):
    account = StringField(validators=[DataRequired(message='The value is not allowed to be empty'), length(
        min=4, max=50
    )])
    pwd = StringField(validators=[DataRequired(message='The value is not allowed to be empty'), length(
        min=4, max=50
    )])
