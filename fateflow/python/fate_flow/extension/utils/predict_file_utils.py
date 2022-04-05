import operator

from fate_flow.extension.model.db_models import DB, PredictFile
from fate_flow.operation.job_saver import str_to_time_stamp


@DB.connection_context()
def predict_file_count():
    count = PredictFile.select().count()
    return count


@DB.connection_context()
def insert_predict(service_id, status, msg, str_time, data_path, context):
    data = PredictFile.create(f_service_id=service_id, f_status=status, f_msg=msg, f_data_path=data_path,
                              f_context=context, f_create_time=str_time)

@DB.connection_context()
def select_by_list(page, page_length):
    predicts = PredictFile.select().paginate(int(page), int(page_length)).order_by(PredictFile.f_create_time.desc())
    predict_list = []
    for predict in predicts:
        data_info = {}
        data_info["f_id"] = predict.f_id
        data_info["f_service_id"] = predict.f_service_id
        data_info["f_msg"] = predict.f_msg
        data_info["f_create_time"] = predict.f_create_time
        data_info["f_status"] = predict.f_status
        data_info["f_context"] = predict.f_context
        data_info["f_data_path"] = predict.f_data_path
        predict_list.append(data_info)
    return predict_list

@DB.connection_context()
def select_by_id(id):
    predict = PredictFile.get_by_id(id)
    data_info = {}
    data_info["f_id"] = predict.f_id
    data_info["f_service_id"] = predict.f_service_id
    data_info["f_msg"] = predict.f_msg
    data_info["f_create_time"] = predict.f_create_time
    data_info["f_status"] = predict.f_status
    data_info["f_context"] = predict.f_context
    data_info["f_data_path"] = predict.f_data_path
    return data_info

@DB.connection_context()
def delete_predict(id):
    PredictFile.delete().where(PredictFile.f_id == id).execute()

@DB.connection_context()
def update_file(service_id, context, str_time, data_path, msg, status):
    PredictFile.update({PredictFile.f_context: context, PredictFile.f_create_time: str_time, PredictFile.f_data_path: data_path,
                        PredictFile.f_msg: msg, PredictFile.f_status: status}).where(PredictFile.f_service_id == service_id).execute()


@DB.connection_context()
def select_by_service_id(service_id):
    predict_file = PredictFile.select().where(PredictFile.f_service_id == service_id).get()
    return predict_file


@DB.connection_context()
def find_status(service_id):
    try:
        data = PredictFile.select().where(PredictFile.f_service_id == service_id).get()
        return {
            "status": data.f_status,
            "retcode": 0,
            "retmsg": "success"
        }
    except:
        response = {
            "retcode": 1,
            "retmsg": "no server_id could be found"
        }
        return response


@DB.connection_context()
def update_status(service_id, status):
    PredictFile.update({PredictFile.f_status: status}).where(PredictFile.f_service_id == service_id).execute()

@DB.connection_context()
def select_by_service_id_count(service_id):
    predicts = PredictFile.select().where(PredictFile.f_service_id==service_id).count()
    return predicts


@DB.connection_context()
def query_predict(reverse=None, order_by=None, **kwargs):
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
            filters.append(getattr(PredictFile, attr_name).between(b_timestamp, e_timestamp))
        elif hasattr(PredictFile, attr_name):
            if f_v=="":
                continue
            else:
                if isinstance(f_v, set):
                    filters.append(operator.attrgetter('f_%s' % f_n)(PredictFile) << f_v)
                else:
                    filters.append(operator.attrgetter('f_%s' % f_n)(PredictFile) == f_v)
    if len(filters)==0:
        predicts = PredictFile.select().order_by(PredictFile.f_create_time.desc())
    else:
        predicts = PredictFile.select().where(*filters).order_by(PredictFile.f_create_time.desc())
        # if reverse is not None:
        #     if not order_by or not hasattr(PredictFile, f"f_{order_by}"):
        #         order_by = "create_time"
        #     if reverse is True:
        #         predicts = predicts.order_by(getattr(PredictFile, f"f_{order_by}").desc())
        #     elif reverse is False:
        #         predicts = predicts.order_by(getattr(PredictFile, f"f_{order_by}").asc())
    list = [predict for predict in predicts]
    page = kwargs.pop('page')
    page_length = kwargs.get('page_length')
    predict_list = paginate_data(int(page), int(page_length), list)
    count = len(list)
    return predict_list, page, page_length, count

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