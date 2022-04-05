#
#  Copyright 2019 The FATE Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
import datetime
import inspect
import os
import sys

from peewee import (CharField, IntegerField, BigIntegerField,
                    TextField, CompositeKey, BigAutoField, BooleanField, PrimaryKeyField)
from playhouse.pool import PooledMySQLDatabase

from fate_arch.common import file_utils
from fate_flow.utils.log_utils import getLogger
from fate_arch.metastore.base_model import JSONField, BaseModel, LongTextField, DateTimeField, SerializedField, \
    SerializedType, ListField
from fate_flow.db.runtime_config import RuntimeConfig
from fate_flow.settings import DATABASE, stat_logger, IS_STANDALONE
from fate_flow.utils.object_utils import from_dict_hook


LOGGER = getLogger()


class JsonSerializedField(SerializedField):
    def __init__(self, object_hook=from_dict_hook, object_pairs_hook=None, **kwargs):
        super(JsonSerializedField, self).__init__(serialized_type=SerializedType.JSON, object_hook=object_hook, object_pairs_hook=object_pairs_hook, **kwargs)


def singleton(cls, *args, **kw):
    instances = {}

    def _singleton():
        key = str(cls) + str(os.getpid())
        if key not in instances:
            instances[key] = cls(*args, **kw)
        return instances[key]

    return _singleton


@singleton
class BaseDataBase(object):
    def __init__(self):
        database_config = DATABASE.copy()
        db_name = database_config.pop("name")
        if IS_STANDALONE:
            from playhouse.apsw_ext import APSWDatabase
            self.database_connection = APSWDatabase(file_utils.get_project_base_directory("fate_sqlite.db"))
            RuntimeConfig.init_config(USE_LOCAL_DATABASE=True)
            stat_logger.info('init sqlite database on standalone mode successfully')
        else:
            self.database_connection = PooledMySQLDatabase(db_name, **database_config)
            stat_logger.info('init mysql database on cluster mode successfully')


class DatabaseLock():
    def __init__(self, lock_name, timeout=10, db=None):
        self.lock_name = lock_name
        self.timeout = timeout
        self.db = db if db else DB

    def lock(self):
        sql = "SELECT GET_LOCK('%s', %s)" % (self.lock_name, self.timeout)
        cursor = self.db.execute_sql(sql)
        ret = cursor.fetchone()
        if ret[0] == 0:
            raise Exception('mysql lock {} is already used'.format(self.lock_name))
        elif ret[0] == 1:
            return True
        else:
            raise Exception('mysql lock {} error occurred!')

    def unlock(self):
        sql = "SELECT RELEASE_LOCK('%s')" % (self.lock_name)
        cursor = self.db.execute_sql(sql)
        ret = cursor.fetchone()
        if ret[0] == 0:
            raise Exception('mysql lock {} is not released'.format(self.lock_name))
        elif ret[0] == 1:
            return True
        else:
            raise Exception('mysql lock {} did not exist.'.format(self.lock_name))

    def __enter__(self):
        if isinstance(self.db, PooledMySQLDatabase):
            self.lock()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if isinstance(self.db, PooledMySQLDatabase):
            self.unlock()


DB = BaseDataBase().database_connection
DB.lock = DatabaseLock


def close_connection():
    try:
        if DB:
            DB.close()
    except Exception as e:
        LOGGER.exception(e)


class DataBaseModel(BaseModel):
    class Meta:
        database = DB


@DB.connection_context()
def init_database_tables():
    members = inspect.getmembers(sys.modules[__name__], inspect.isclass)
    table_objs = []
    for name, obj in members:
        if obj != DataBaseModel and issubclass(obj, DataBaseModel):
            table_objs.append(obj)
    DB.create_tables(table_objs)


def fill_db_model_object(model_object, human_model_dict):
    for k, v in human_model_dict.items():
        attr_name = 'f_%s' % k
        if hasattr(model_object.__class__, attr_name):
            setattr(model_object, attr_name, v)
    return model_object


class Predict(DataBaseModel):
    f_id = PrimaryKeyField()
    f_name = CharField(max_length=50, index=True)
    f_service_id = IntegerField(index=True, null=True)
    f_data_path = CharField(max_length=100, null=True)
    f_score_path = CharField(max_length=100, null=True)
    f_context = TextField(null=True, default='')
    f_status = CharField(max_length=50, index=True)
    f_msg = CharField(max_length=25, index=True)

    class Meta:
        db_table = "t_predict"


class User(DataBaseModel):
    id = PrimaryKeyField()
    f_account = CharField(max_length=50, index=True)
    f_pwd = CharField(max_length=250, index=True)
    f_nickname = CharField(max_length=50, index=True)
    f_party_id = CharField(max_length=50, index=True)
    # f_phone = CharField(max_length=50, index=True)
    # f_email = CharField(max_length=50, index=True)

    class Meta:
        db_table = "t_user"


class Deploy(DataBaseModel):
    f_id = PrimaryKeyField()
    f_service_id = IntegerField(index=True, null=True)
    f_model_id = CharField(max_length=25, index=True, null=True)
    f_location = IntegerField(index=True, null=True)
    f_context = TextField(null=True, default='')
    f_status = CharField(max_length=50, index=True)
    f_msg = CharField(max_length=25, index=True)

    class Meta:
        db_table = "t_deploy"


class PredictFile(DataBaseModel):
    f_id = PrimaryKeyField()
    f_service_id = IntegerField(index=True, null=True)
    f_data_path = CharField(max_length=100, index=True)
    f_context = TextField(null=True, default='')
    f_status = CharField(max_length=50, index=True)
    f_msg = CharField(max_length=25, index=True)

    class Meta:
        db_table = "t_predict_file"